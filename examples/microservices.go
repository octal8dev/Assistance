package main

import (
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/your-org/voltage/pkg/client"
)

// Microservice message structure
type ServiceMessage struct {
	ServiceID   string                 `json:"service_id"`
	RequestID   string                 `json:"request_id"`
	Timestamp   time.Time              `json:"timestamp"`
	Action      string                 `json:"action"`
	Data        map[string]interface{} `json:"data"`
	Signature   string                 `json:"signature"`
}

func main() {
	fmt.Println("🔧 Voltage Microservices Demo")
	
	// Create clients for different microservices
	authService, err := client.New(client.Config{EnableCompression: true})
	if err != nil {
		log.Fatal("Failed to create auth service:", err)
	}
	defer authService.Close()
	
	userService, err := client.New(client.Config{EnableCompression: true})
	if err != nil {
		log.Fatal("Failed to create user service:", err)
	}
	defer userService.Close()
	
	// Establish secure channel
	handshake, _ := authService.StartHandshake()
	response, _ := userService.ProcessHandshake(handshake)
	authService.CompleteHandshake(response)
	
	fmt.Println("🔐 Secure inter-service channel established!")
	
	// Auth service sends user authentication request
	authRequest := ServiceMessage{
		ServiceID: "auth-service-001",
		RequestID: "req_12345",
		Timestamp: time.Now(),
		Action:    "validate_user",
		Data: map[string]interface{}{
			"user_id": "user_67890",
			"token":   "jwt_token_here",
			"scope":   []string{"read", "write"},
		},
	}
	
	// Encrypt and send
	authJSON, _ := json.Marshal(authRequest)
	encryptedAuth, err := authService.Encrypt(authJSON)
	if err != nil {
		log.Fatal("Failed to encrypt auth request:", err)
	}
	
	fmt.Println("📤 Auth request sent securely")
	
	// User service receives and processes
	decryptedAuth, err := userService.Decrypt(encryptedAuth)
	if err != nil {
		log.Fatal("Failed to decrypt auth request:", err)
	}
	
	var receivedRequest ServiceMessage
	json.Unmarshal(decryptedAuth, &receivedRequest)
	
	fmt.Printf("📥 User Service received: %s from %s\n", receivedRequest.Action, receivedRequest.ServiceID)
	
	// User service responds
	authResponse := ServiceMessage{
		ServiceID: "user-service-001",
		RequestID: receivedRequest.RequestID, // Same request ID
		Timestamp: time.Now(),
		Action:    "user_validated",
		Data: map[string]interface{}{
			"valid":      true,
			"user_id":    "user_67890",
			"username":   "voltage_user",
			"permissions": []string{"read", "write", "admin"},
			"expires_at": time.Now().Add(24 * time.Hour),
		},
	}
	
	// Encrypt response
	responseJSON, _ := json.Marshal(authResponse)
	encryptedResponse, err := userService.Encrypt(responseJSON)
	if err != nil {
		log.Fatal("Failed to encrypt response:", err)
	}
	
	// Auth service receives response
	decryptedResponse, err := authService.Decrypt(encryptedResponse)
	if err != nil {
		log.Fatal("Failed to decrypt response:", err)
	}
	
	var finalResponse ServiceMessage
	json.Unmarshal(decryptedResponse, &finalResponse)
	
	fmt.Printf("✅ Auth Service received: %s\n", finalResponse.Action)
	fmt.Printf("📊 User validation result: %v\n", finalResponse.Data["valid"])
	
	// Demo heartbeat between services
	fmt.Println("\n💓 Testing service heartbeat...")
	
	heartbeat, _ := authService.CreateHeartbeat()
	fmt.Printf("Heartbeat sent from %s\n", authRequest.ServiceID)
	
	fmt.Println("\n🎉 Microservices secure communication demo completed!")
}
