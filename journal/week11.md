# Week 11 — CloudFormation Part 2





















## Save the work on its own branch named "week-11"
```sh
cd aws-bootcamp-cruddur-2024
git checkout -b week-11
```
<hr/>

## Commit
Add the changes and create a commit named: "CloudFormation Part 2"
```sh
git add .
git commit -m "CloudFormation Part 2"
```
Push your changes to the branch
```sh
git push origin week-11
```
<hr/>

### Tag the commit
```sh
git tag -a week-11 -m "Setting up CloudFormation Part 2"
```
<hr/>

### Push your tags
```sh
git push --tags
```
<hr/>

### Switching Between Branches back to Main
```sh
git checkout main
```
<hr/>

### Merge Changes
```sh
git merge week-11
```
<hr/>

### Push Changes to Main
```sh
git push origin main
```
<hr/>

#### Branches?
If you want to keep the "week-1" branch for future reference or additional work, 
you can keep it as is. If you no longer need the branch, you can delete it after merging.
```sh
git branch -d week-11  # Deletes the local branch
git push origin --delete week-11  # Deletes the remote branch
```