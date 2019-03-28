# connectED-backend

work flow:

1) make edits

2) create open-api doc 

``` python lib/endpoints/endpointscfg.py get_openapi_spec connected.connectEDApi --hostname connected-dev-214119.appspot.com ```

**Convert the doc to yaml format using swagger editor, replace the contents in swaggerDEPLOY.yaml with the contents of the converted doc, then add the necessary data from swggerTEMPLATE.yaml to swaggerDEPLOY.yaml

3) deploy app.yaml doc to Google App Engine

``` gcloud app deploy app.yaml --project connected-dev-214119 ```

4) deploy finalized swagger doc to Google Cloud Endpoints

``` gcloud endpoints services deploy swaggerDEPLOY.yaml ```

