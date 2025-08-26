package main

import (
	"encoding/json"
	"fmt"
	"log"

	"github.com/your-org/voltage/pkg/client"
	"github.com/your-org/voltage/internal/protocol"
)

// AI Assistant Message example
type AIMessage struct {
	ID       string `json:"id"`
	Role     string `json:"role"`     // "user" or "assistant"
	Content  string `json:"content"`
	Model    string `json:"model"`
	Tokens   int    `json:"tokens"`
}

func main() {
	fmt.Println("🤖 Voltage AI Assistant Demo")
	
	// Create secure clients for AI communication
	clientA, err := client.New(client.Config{
		EnableCompression: true,
	})
	if err != nil {
		log.Fatal("Failed to create client:", err)
	}
	defer clientA.Close()
	
	clientB, err := client.New(client.Config{
		EnableCompression: true,
	})
	if err != nil {
		log.Fatal("Failed to create assistant:", err)
	}
	defer clientB.Close()
	
	// Perform handshake
	handshake, _ := clientA.StartHandshake()
	response, _ := clientB.ProcessHandshake(handshake)
	clientA.CompleteHandshake(response)
	
	fmt.Println("🔐 Secure channel established!")
	
	// Simulate AI conversation
	userMessage := AIMessage{
		ID:      "msg_001",
		Role:    "user",
		Content: "Объясни принципы работы криптографического протокола Voltage",
		Model:   "gpt-4",
		Tokens:  0,
	}
	
	// Serialize and encrypt user message
	userJSON, _ := json.Marshal(userMessage)
	encryptedUser, err := clientA.Encrypt(userJSON)
	if err != nil {
		log.Fatal("Failed to encrypt user message:", err)
	}
	
	fmt.Println("📨 User message encrypted and sent")
	
	// "Assistant" receives and decrypts
	decryptedUser, err := clientB.Decrypt(encryptedUser)
	if err != nil {
		log.Fatal("Failed to decrypt user message:", err)
	}
	
	var receivedMessage AIMessage
	json.Unmarshal(decryptedUser, &receivedMessage)
	
	fmt.Printf("👤 User: %s\n", receivedMessage.Content)
	
	// Assistant response
	assistantMessage := AIMessage{
		ID:   "msg_002",
		Role: "assistant",
		Content: `Voltage Protocol - это высокопроизводительный криптографический протокол, основанный на принципах MTProto, но оптимизированный для современных приложений:

🔑 Ключевые компоненты:
- ECDH P-256 для обмена ключами
- AES-256-GCM для симметричного шифрования
- HMAC-SHA256 для аутентификации сообщений
- Опциональное сжатие данных (zstd)

🛡️ Безопасность:
- Perfect Forward Secrecy через ECDH
- Защита от replay-атак через временные метки
- Целостность данных через HMAC

⚡ Производительность:
- Минимальные накладные расходы
- Быстрое шифрование/дешифрование
- Эффективное сжатие для больших данных

Протокол идеально подходит для микросервисов, AI-приложений и реал-тайм коммуникаций.`,
		Model:  "voltage-ai",
		Tokens: 245,
	}
	
	// Encrypt assistant response
	assistantJSON, _ := json.Marshal(assistantMessage)
	encryptedAssistant, err := clientB.Encrypt(assistantJSON)
	if err != nil {
		log.Fatal("Failed to encrypt assistant message:", err)
	}
	
	// Client A receives response
	decryptedAssistant, err := clientA.Decrypt(encryptedAssistant)
	if err != nil {
		log.Fatal("Failed to decrypt assistant message:", err)
	}
	
	var assistantResponse AIMessage
	json.Unmarshal(decryptedAssistant, &assistantResponse)
	
	fmt.Printf("\n🤖 Assistant: %s\n", assistantResponse.Content)
	fmt.Printf("\n📊 Tokens used: %d\n", assistantResponse.Tokens)
	
	fmt.Println("\n✅ Secure AI conversation completed!")
}
