#!/usr/bin/env sh
set -xe

helm lint chart/price_service -f chart/price_service/values.yaml -f chart/price_service/values.dev.yaml
helm lint chart/price_service -f chart/price_service/values.yaml -f chart/price_service/values.pre-prod.yaml
helm lint chart/price_service -f chart/price_service/values.yaml -f chart/price_service/values.prod.yaml
