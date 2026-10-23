$repo = "ai-ml-devsecops/devsec"

gh pr list -R $repo --state all --limit 200 `
  --json number,title,state,isDraft,author `
  --jq '.[] | select(.isDraft | not) | [.number, .state, .author.login, .title] | @tsv'