# ================================
# Makefile for Citation Timeline
# ================================

PYTHON := python3
SCRIPT := fetch_citation_timeline.py

OUTPUT_DIR := citation_timeline

.DEFAULT_GOAL := run

# Run the crawler
run:
	@echo "🚀 Starting citation timeline crawler..."
	$(PYTHON) $(SCRIPT)

# Clean cache and intermediate data
clean:
	@echo "🧹 Cleaning previous cached data..."
	rm -rf $(OUTPUT_DIR)
	@echo "✔ Cleaned."

# Full restart (clean + run)
restart: clean run
