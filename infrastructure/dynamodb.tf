# Single table for every resume entity — see docs/projects/resume-api/design.md
# for the pk/sk scheme. Every access pattern here is "everything for one
# person," so one table with a composite key covers it; no GSIs needed.

resource "aws_dynamodb_table" "resume" {
  name         = "resume-api"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }
}
