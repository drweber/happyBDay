# Happy BirthDay App
It is test REST Api app which response how many days till BDay
All response in JSON format 
It is possible add new users to DB and update existed user profile

### GET information about user
```
GET /hello/<username>
``` 
#### Response
`404` Not Found if the user does not exist
`200` OK on success

### PUT information about user
```
PUT /hello/<username> {"dateOfBirth": "YYYY-MM-DD"}
``` 
input validation by JSON schema implemented and 
Date validate by regexp expression mathes dates formatted as `YYYY-MM-DD` from `0000-01-01` to `9999-12-31`. It checks leap year including all modulo `400`, modulo `100` and modulo `4` rules
#### Response
`201` Created if the user does not exist 
`204` No Content if the user exist

### If method not support
```
POST /hello/<username> {"dateOfBirth": "YYYY-MM-DD"}
```
#### Response
`405` Not Allowed if method is not allowed

# Deploy in Cloud, bare-metal, local environment

This app is prepared to deploy in any Kubernetes environment. It could be EKS, GKE, AKS and etc. as well as bare-metal and local minikube. Details are below.
In shot description ypu just need K8S cluster and it is doesn't matter where it will be. 

#### Not included here but exist and fully tested
I have prepared Terraform modules to create K8S clusters in GKE and EKS and fully automates this circle from scratch with initiated release from described APP and it is also provide Let's Encrypt SSL certificated
in Summary:
```bash
terrafrom apply
```
Will make
 - Terraform will create kubernetes cluster (EKS or GKE)
 - will deploy Flux into it
 - Flux will deploy helm chart with Application
 - Terraform create DNS record (AWS or Google)
 - Terraform install Cert-Manager 
 - Cert-manager will request certificate (staging or produstion) and apply it to current infrastructure
 - Fully deployed API ready by HTTPS

## Managing Helm releases the GitOps way

**What is GitOps?**

GitOps is a way to do Continuous Delivery, it works by using Git as a source of truth for declarative infrastructure and workloads. 
For Kubernetes this means using `git push` instead of `kubectl create/apply` or `helm install/upgrade`.

In a traditional CICD pipeline, CD is an implementation extension powered by the 
continuous integration tooling to promote build artifacts to production. 
In the GitOps pipeline model, any change to production must be committed in source control 
(preferable via a pull request) prior to being applied on the cluster. 
This way rollback and audit logs are provided by Git. 
If the entire production state is under version control and described in a single Git repository, when disaster strikes, 
the whole infrastructure can be quickly restored from that repository.

To better understand the benefits of this approach to CD and what the differences between GitOps and 
Infrastructure-as-Code tools are, head to the Weaveworks website and read [GitOps - What you need to know](https://www.weave.works/technologies/gitops/) article.

In order to apply the GitOps pipeline model to Kubernetes you need three things: 

* a Git repository with your workloads definitions in YAML format, Helm charts and any other Kubernetes custom resource that defines your cluster desired state (I will refer to this as the *config* repository)
* a container registry where your CI system pushes immutable images (no *latest* tags, use *semantic versioning* or git *commit sha*)
* an operator that runs in your cluster and does a two-way synchronization:
    * watches the registry for new image releases and based on deployment policies updates the workload definitions with the new image tag and commits the changes to the config repository 
    * watches for changes in the config repository and applies them to your cluster

I will be using GitHub to host the config repo, Docker Hub as the container registry and Flux as the GitOps Kubernetes Operator.

![gitops](./pics/flux-helm-operator-registry.jpg?raw=true)

### Install Helm and Tiller

If you don't have Helm CLI installed, on macOS you can use `brew install kubernetes-helm`.   

Create a service account and a cluster role binding for Tiller: 

```bash
kubectl -n kube-system create sa tiller

kubectl create clusterrolebinding tiller-cluster-rule \
    --clusterrole=cluster-admin \
    --serviceaccount=kube-system:tiller 
```

Note that on GKE you need to create an admin cluster user for yourself:

```bash
kubectl create clusterrolebinding "cluster-admin-$(whoami)" \
    --clusterrole=cluster-admin \
    --user="$(gcloud config get-value core/account)"
```

Deploy Tiller in kube-system namespace:

```bash
helm init --skip-refresh --upgrade --service-account tiller
```

### Install Flux

The first step in automating Helm releases with [Flux](https://github.com/weaveworks/flux) is to create a Git repository with your charts source code.
You can fork this repository and use it as a template for your cluster config.

*If you fork, update the release definitions with your Docker Hub repository and GitHub username located in 
\releases\(dev/stg/prod)\happy.yaml in your master branch before proceeding.

Apply the Helm Release CRD:

```bash
kubectl apply -f https://raw.githubusercontent.com/fluxcd/flux/master/deploy-helm/flux-helm-release-crd.yaml
```

Add the Flux chart repo:

```bash
helm repo add fluxcd https://charts.fluxcd.io
```

Install Flux and its Helm Operator by specifying your fork URL 
(replace `drweber` with your GitHub username): 

```bash
helm install --name flux \
--set rbac.create=true \
--set helmOperator.create=true \
--set git.url=git@github.com:drweber/happyBDay \
--namespace flux \
fluxcd/flux
```

The Flux Helm operator provides an extension to Flux that automates Helm Chart releases for it. 
A Chart release is described through a Kubernetes custom resource named HelmRelease.
The Flux daemon synchronizes these resources from git to the cluster, 
and the Flux Helm operator makes sure Helm charts are released as specified in the resources.

Note that Flux Helm Operator works with Kubernetes 1.9 or newer. 

At startup Flux generates a SSH key and logs the public key. 
Find the SSH public key with:

```bash
kubectl -n flux logs deployment/flux | grep identity.pub | cut -d '"' -f2
```

In order to sync your cluster state with Git you need to copy the public key and 
create a **deploy key** with **write access** on your GitHub repository.

Open GitHub, navigate to your fork, go to _Setting > Deploy keys_ click on _Add deploy key_, check 
_Allow write access_, paste the Flux public key and click _Add key_.

### Check that everything is working correct
Create port-forward from remote service `happy-backend` and remote port `8080` to local `127.0.0.1:8080`
```bash
kubectl port-forward svc/happy-backend 8080:8080 -n dev
```

### GitOps pipeline example

I will be using [Happy-BirthDay](https://github.com/drweber/happyBDay/app) to demonstrate a full CI/CD pipeline including promoting releases between environments.

I'm assuming the following Git branching model:
* dev branch (feature-ready state)
* stg branch (release-candidate state)
* master branch (production-ready state)

When a PR is merged in the dev or stg branch will produce a immutable container image as in `repo/app:branch-commitsha`.

Inside the *root* dir you can find a script that simulates the CI process for dev and stg. 
The *ci-mock.sh* script does the following:
* pulls the Happy-BirthDay source code from GitHub
* generates a random string and modifies the code
* generates a random Git commit short SHA
* builds a Docker image with the format: `yourname/happy:branch-sha`
* pushes the image to Docker Hub

Let's create an image corresponding to the `dev` branch (replace `drweber` with your Docker Hub username):

```bash
╰ ./ci-mock.sh -r drweber -a happy -b dev
>>>> Building image drweber/happy:dev-cpemo4h2 <<<<
Sending build context to Docker daemon    619kB
Step 1/8 : FROM python:3.7
 ---> 14a2caeca327
Step 2/8 : WORKDIR /usr/src/
....
Step 8/8 : CMD ["gunicorn", "-b 0.0.0.0:8080", "wsgi:app.app"]
....
Successfully built 9d6379b017b0
Successfully tagged drweber/happy:dev-cpemo4h2
The push refers to repository [docker.io/drweber/happy]
63a90afcddc8: Pushed
```

Detailed information about how GitOps works in [article](https://dzone.com/articles/managing-helm-releases-the-gitops-way) by [Stefan Prodan](https://stefanprodan.com) . 