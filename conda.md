## Create a new environment

```
conda create --name <name>
```

## Activate the environment

```
conda activate <name>
```

## Deactivate the environment

```
conda deactivate
```

## Save the environment

```
conda env export > environment.yml
```

## Load the environment

```
conda env create -f environment.yml
```

## Update the environment

```
conda env update -f environment.yml
```
