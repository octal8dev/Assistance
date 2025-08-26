VOLTAGE_VERSION := 1.0.0
GO_VERSION := 1.21

.PHONY: all build test clean demo examples fmt vet deps

all: deps fmt vet test build

# Install dependencies
deps:
	go mod download
	go mod tidy

# Format code
fmt:
	go fmt ./...

# Vet code
vet:
	go vet ./...

# Run tests
test:
	go test -v ./...

# Run benchmarks
bench:
	go test -bench=. -benchmem ./...

# Build all examples
build:
	go build -o bin/demo ./cmd/demo
	go build -o bin/server ./cmd/server
	go build -o bin/ai_assistant ./examples/ai_assistant.go
	go build -o bin/microservices ./examples/microservices.go

# Run demo
demo:
	go run ./cmd/demo

# Run AI assistant example
ai:
	go run ./examples/ai_assistant.go

# Run microservices example
micro:
	go run ./examples/microservices.go

# Clean build artifacts
clean:
	rm -rf bin/
	go clean

# Run all examples
examples: demo ai micro

# Generate docs
docs:
	godoc -http=:6060

# Check for vulnerabilities
security:
	go list -json -m all | docker run --rm -i sonatypecommunity/nancy:latest sleuth

# Docker build
docker:
	docker build -t voltage:$(VOLTAGE_VERSION) .

# Release
release: clean deps fmt vet test build
	@echo "✅ Release $(VOLTAGE_VERSION) ready!"
