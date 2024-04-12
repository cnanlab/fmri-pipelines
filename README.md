This is a repo for fMRI pipelines created for the CNAN lab at UTD. Currently just has a simple
preprocessing and a randomise (HLA) pipeline.

## Structure
[/preprocess](preprocess)

Handles a simple preprocessing pipeline via FSL, including brain extraction (BET). Configuration is handled via a 
design.fsf file, which is a template for the FEAT GUI. 


[/randomise](randomise)

Handles a simple randomise pipeline via FSL. 