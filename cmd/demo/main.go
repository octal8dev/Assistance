package main

import (
	"fmt"
	"log"

	"github.com/your-org/voltage/pkg/client"
)

func main() {
	fmt.Println("🔥 Voltage Protocol Demo")
	
	// Create two clients for demonstration
	clientA, err := client.New(client.Config{
		EnableCompression: true,
	})
	if err != nil {
		log.Fatal("Failed to create client A:", err)
	}
	defer clientA.Close()
	
	clientB, err := client.New(client.Config{
		EnableCompression: true,
	})
	if err != nil {
		log.Fatal("Failed to create client B:", err)
	}
	defer clientB.Close()
	
	fmt.Println("✅ Created two clients")
	
	// Perform handshake
	fmt.Println("🤝 Starting handshake...")
	
	// Client A starts handshake
	handshakeMsg, err := clientA.StartHandshake()
	if err != nil {
		log.Fatal("Failed to start handshake:", err)
	}
	
	// Client B processes handshake and responds
	responseMsg, err := clientB.ProcessHandshake(handshakeMsg)
	if err != nil {
		log.Fatal("Failed to process handshake:", err)
	}
	
	// Client A completes handshake
	err = clientA.CompleteHandshake(responseMsg)
	if err != nil {
		log.Fatal("Failed to complete handshake:", err)
	}
	
	fmt.Println("✅ Handshake completed!")
	fmt.Printf("Client A connected: %v\n", clientA.IsConnected())
	fmt.Printf("Client B connected: %v\n", clientB.IsConnected())
	
	// Test encrypted communication
	fmt.Println("\n🔐 Testing encrypted communication...")
	
	originalMessage := "Hello from Voltage Protocol! 🚀 This is a secure message."
	
	// Client A encrypts message
	encryptedMsg, err := clientA.Encrypt([]byte(originalMessage))
	if err != nil {
		log.Fatal("Failed to encrypt message:", err)
	}
	
	fmt.Printf("Original: %s\n", originalMessage)
	fmt.Printf("Encrypted payload size: %d bytes\n", len(encryptedMsg.Payload))
	
	// Client B decrypts message
	decryptedData, err := clientB.Decrypt(encryptedMsg)
	if err != nil {
		log.Fatal("Failed to decrypt message:", err)
	}
	
	fmt.Printf("Decrypted: %s\n", string(decryptedData))
	
	if string(decryptedData) == originalMessage {
		fmt.Println("✅ Encryption/Decryption successful!")
	} else {
		fmt.Println("❌ Encryption/Decryption failed!")
	}
	
	// Test heartbeat
	fmt.Println("\n💓 Testing heartbeat...")
	
	heartbeat, err := clientA.CreateHeartbeat()
	if err != nil {
		log.Fatal("Failed to create heartbeat:", err)
	}
	
	fmt.Printf("Heartbeat type: %d, payload: %s\n", heartbeat.Type, string(heartbeat.Payload))
	
	fmt.Println("🎉 Demo completed successfully!")
}
