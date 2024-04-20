#!/bin/bash

echo "Removing crash files"
rm -i workingdir/crash/*

echo "Removing workflow directory in workingdir"
rm -ri workingdir/preproc_FEAT_workflow