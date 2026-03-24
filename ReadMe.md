# Copy example to .env
cp .env.example .env
# Edit .env with your values
# Or set environment variables
export BUZZER_ADMIN_SESSION="your-token"
export BUZZER_INSTANCE="your-instance"
# Or use command line arguments
python jeopardy.py --instance my-game --admin-session my-token --question-dir my-questions