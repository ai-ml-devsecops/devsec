token_value = "glpat-devsecbootstra"
user = User.find_by_username("root")
raise "root user was not found" unless user

user.personal_access_tokens.where(name: "devsecops-lab-bootstrap").delete_all
token = user.personal_access_tokens.create!(
  name: "devsecops-lab-bootstrap",
  scopes: ["api", "create_runner"],
  expires_at: 1.year.from_now,
)
token.set_token(token_value)
token.save!
puts token_value
