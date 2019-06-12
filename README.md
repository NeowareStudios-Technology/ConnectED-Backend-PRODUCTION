# connectED-backend

## Get started on local development environment
- Follow [this guide](https://cloud.google.com/python/setup) to get Python development environment setup on machine
- Start the local development server using
  `dev_appserver.py app.yaml`
- Send requests to the local development server using Postman or curl at `http://localhost:8080`

## Work flow:

1) Edit routes in connected.py and models.py
2) create open-api doc
  ```
  python lib/endpoints/endpointscfg.py get_openapi_spec connected.connectEDApi --hostname connected-dev-214119.appspot.com
  ```
  ** Convert the doc to yaml format using [swagger editor](https://editor.swagger.io/), replace the contents in swaggerDEPLOY.yaml with the contents of the converted doc, then add/replace the data from swggerTEMPLATE.yaml to swaggerDEPLOY.yaml
3) deploy app.yaml doc to Google App Engine
  ```
  gcloud app deploy app.yaml --project connected-dev-214119
  ```
4) deploy finalized swagger doc to Google Cloud Endpoints
  ```
  gcloud endpoints services deploy swaggerDEPLOY.yaml
  ```
