#!/bin/bash

# dependency update for bot deps
VENV_ACTIVATE='source ~/raidbotenv/bin/activate'
# shellcheck disable=SC2016
UPDATE_BOT_DEPS='[[ $(pip list --outdated --format=freeze | grep -v '\''^\-e'\'' | cut -d = -f 1) != "" ]] && '\
'pip list --outdated --format=freeze | grep -v '\''^\-e'\'' | cut -d = -f 1  | xargs -n1 pip install -U || '\
'echo Dependencies are up to date.'

#echo "$VENV_ACTIVATE && $UPDATE_BOT_DEPS"

RESTART_BOT="sudo systemctl restart raidbot && exit"

# deploy to gcloud
echo Deploying to gcloud...
gcloud compute scp --recurse raidbot/ raid-applicants-distributor-vm-instance:/home/nickb/raidbot

# update python deps for bot on gcloud
# shellcheck disable=SC2090
echo Updating dependencies...
gcloud compute ssh raid-applicants-distributor-vm-instance --zone=us-east1-b --command="$VENV_ACTIVATE && $UPDATE_BOT_DEPS"
# restart bot on gcloud
echo Restarting bot...
gcloud compute ssh raid-applicants-distributor-vm-instance --zone=us-east1-b --command="$RESTART_BOT"

echo Done!
