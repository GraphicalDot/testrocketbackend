#!/bin/bash
git push heroku-stag dev:master
heroku pg:reset HEROKU_POSTGRESQL_AMBER_URL -a testrocket-api-staging --confirm testrocket-api-staging
heroku pgbackups:transfer testrocket-api::MAROON HEROKU_POSTGRESQL_AMBER_URL -a testrocket-api-staging --confirm testrocket-api-staging