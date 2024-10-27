# data-pipeline-lambda-function

This repository contains the Lambda functions that are used in data pipelines.  

The Lambda functions are in the `lambda` directory.  For descriptions of each Lambda function, see the README.md file 
in the corresponding directory.

The Terraform code is used to deploy the Lambda functions to AWS.  The Terraform code is located in the `terraform`.

---

## Release Workflow

All changes should have a Jira ticket associated with the change, no exception.

1. Create a new branch from `main` with a branch name that is unique to your Jira ticket. Make changes in your branch.
2. Be sure to include an appropriate commit title following this format: <br>
   `<commit-type>: [ABC-123] Does things for widgets` <br>
   Where commit-type should be one of the following:<br>
   ```
   fix: a patch fix release
   feat: a minor/feature release
   perf: a major/breaking change release
   ```
   for example: <br>
    1. A patch fix release: <br>
       `fix: [ABC-123] Added a smiley face to the response`
    2. A minor/feature release:
       `feat: [ABC-123] Updated the workflow to correctly process penguin emojis in messages`
    3. A major release with breaking changes:
       `perf: [ABC-123] Changed the output format of the response writing into the landing zone`
3. Within the feature branch, validate the changes to tst env in CircleCI.  If the changes are not passing, fix the  
   issues in the feature branch.
4. Create a PR from your branch.  Be sure to include the Jira ticket number in the PR title.  For example: <br>
    `[ABC-123] Updating penguin ingress lambda function`
5. When PR is approved and merged to main, the CI/CD pipeline will automatically deploy the changes to the tst 
   environment.  
    1. Note: if you're squashing the commits, be sure to include appropriate semantic versioning keywords in
       the commit message.
6. In the CircleCI pipeline there will be a manual approval step to create a release tag.  Anyone can approve the
   creation of a release tag.  If there is any commit message that includes the semantic versioning keywords, the 
   pipeline will automatically create a release tag.
    1. Alternatively, we can manually create a release tag, this is not recommended. 
7. Once a release tag is created, a workflow will trigger an approval to deploy to production.  A release message will
   be posted to the `#release-coordination` Slack channel for visibility.  Any EM or technical lead can approve this.
8. Once deployment is approved, the tagged release will be deployed to the prd environment.
    1. A release message will be posted to the `#releases` Slack channel.  The format of the message is stored as an
       environment variable `DATA_PIPELINE_RELEASE_MESSAGE` in the CircleCI project.


---

