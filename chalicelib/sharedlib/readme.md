# Sharedlib

Este repositório tem as funcões mais usadas nos projetos que usam chalice. 

Deve ser criado como um summodulo dentro da pasta chalicelib.


## Pre requisitos

Depende da existencia do `chalice.app`

## Como instalar

1. Entrar no diretório `chalicelib`
2. Dentro deste diretório, rodar o comando 

```bash
git submodule add git@bitbucket.org:Empiricusind/al-sharedlib.git sharedlib
```

Isso irá criar o diretório `sharedlib` dentro do chalicelib. 

## Como atualizar: 

Entrar dentro do diretório do submódulo, e rodar o comando `git pull`

ou 

dentro do repositorio, rodar o comando `git submodule foreach git pull`.

## Notas: 

- cada submodulo se comporta como um clone do repositorio indicado; portanto, alterações feitas no submódulo podem ser registradas (add, commit) e publicadas (push)

## ultima alteração: 11/maio, 15:36
