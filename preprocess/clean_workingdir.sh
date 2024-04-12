#!/bin/bash

echo "Removing crash files"
rm workingdir/crash/*

echo "Removing workflow directory in workingdir"
rm -r workingdir/preproc_FEAT_workflow