#!/bin/bash
rsync -av --progress --exclude='config.json' --exclude='.git' --exclude='venv' --exclude='__pycache__' . ../QuantOS_Private/
echo "✅ Deployed v2.0.0 to Private Bot."
