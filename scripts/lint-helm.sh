#!/usr/bin/env sh
set -xe

helm lint chart/product-price -f chart/product-price/values.yaml -f chart/product-price/values.dev.yaml
helm lint chart/product-price -f chart/product-price/values.yaml -f chart/product-price/values.pre-prod.yaml
helm lint chart/product-price -f chart/product-price/values.yaml -f chart/product-price/values.prod.yaml
