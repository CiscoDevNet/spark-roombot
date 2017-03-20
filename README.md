# spark-roombot

Spark roombot is the logic behind a spark developer API Key (developer.ciscospark.com) to allow a self-service portal for users to add themselves to spark rooms (for use cases such as help and support, etc).

It includes a sample web interface (client side) for excercising the back-end REST API.

Whitelisting rooms and blacklisting users is currently supported.
Persistence for the above lists is acheived through Kubernetes ConfigMap's (see deployment section below).

## Dependancies
* Python3
* flask
* validate_email
* flask-cors

These are captured in `requirements.txt` so `pip install -r requirements.txt` will do the right thing.

## Deployment

This repository is designed to run on Kubernetes. First the application is packaged into a container using the included `Dockerfile`, this Dockerfile is based on a Nginx + uwsgi + flask setup. It expects the flask app to be called 'app' and a `main.py` to be in the containers `/app` directory at runtime.

The container includes supervisord to handle nginx and uwsgi startup.

Once the container image is available in a Docker repository, (in our case dockerhub: trxuk/devnet-spark-roomaddbot), the `k8s` repository contains all the required manifests to deploy the application onto a kubernetes cluster.

For persistence and management of whitelists and blacklists, we use kubernetes ConfigMaps, see the `k8s/configmap.yaml` file. Note you will need to include your own developer.ciscospark.com BOT API key after `accessToken =` before deploying this application to kubernetes.

Then simply (assuming you have a working kubectl command on your machine);

```
for i in namespace.yaml configmap.yaml service.yaml ingress.yaml deployment.yaml ; do kubectl create -f $i ; done
```

This will deploy the necessary components.
Notice the ingress controller and it's annotations. Our kubernetes cluster automatically sets up public DNS and SSL certificates where needed. For more information on achieving this generally in kubernetes, see [http://www.matt-j.co.uk/2017/03/03/automatic-dns-and-ssl-on-kubernetes-with-letsencrypt-part-1/]()


### Code Updates
To update the code for production you would;

* Make code changes
* `docker build .` to create a new image
* `docker tag <containerid> trxuk/devnet-spark-roomaddbot:version` to create a newer version of the container image
* `docker push trxuk/devnet-spark-roomaddbot:version` to make the new image available on dockerhub
* Bump the `image:` version in `k8s/deployment.yaml` to the newer image version
* `kubectl replace -f k8s/deployment.yaml` to have kubernetes deploy the new application version.
