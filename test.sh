#!/bin/sh
#
#
curl -X POST -H "Content-Type: application/json" -d @./test_data00.json localhost:8080/check_temp
curl -X POST -H "Content-Type: application/json" -d @./test_data01.json localhost:8080/check_temp
curl -X POST -H "Content-Type: application/json" -d @./test_data02.json localhost:8080/check_temp
curl -X POST -H "Content-Type: application/json" -d @./test_data03.json localhost:8080/check_temp
curl -X POST -H "Content-Type: application/json" -d @./test_data04.json localhost:8080/check_temp
