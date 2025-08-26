package crypto

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"fmt"
	"io"

	"github.com/your-org/voltage/internal/protocol"
)

// Encryptor handles AES-256-GCM encryption
type Encryptor struct {
	key []byte
}

// NewEncryptor creates a new encryptor with the given key
func NewEncryptor(key []byte) (*Encryptor, error) {
	if len(key) != protocol.KeySize {
		return nil, fmt.Errorf("invalid key size: expected %d, got %d", protocol.KeySize, len(key))
	}
	
	return &Encryptor{key: key}, nil
}

// Encrypt encrypts data using AES-256-GCM
func (e *Encryptor) Encrypt(data []byte) ([]byte, error) {
	// Create AES cipher
	block, err := aes.NewCipher(e.key)
	if err != nil {
		return nil, fmt.Errorf("failed to create cipher: %w", err)
	}
	
	// Create GCM mode
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("failed to create GCM: %w", err)
	}
	
	// Generate random nonce
	nonce := make([]byte, protocol.NonceSize)
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return nil, fmt.Errorf("failed to generate nonce: %w", err)
	}
	
	// Encrypt and prepend nonce
	ciphertext := gcm.Seal(nonce, nonce, data, nil)
	return ciphertext, nil
}

// Decrypt decrypts data using AES-256-GCM
func (e *Encryptor) Decrypt(data []byte) ([]byte, error) {
	if len(data) < protocol.NonceSize {
		return nil, protocol.ErrInvalidMessage
	}
	
	// Create AES cipher
	block, err := aes.NewCipher(e.key)
	if err != nil {
		return nil, fmt.Errorf("failed to create cipher: %w", err)
	}
	
	// Create GCM mode
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("failed to create GCM: %w", err)
	}
	
	// Extract nonce and ciphertext
	nonce := data[:protocol.NonceSize]
	ciphertext := data[protocol.NonceSize:]
	
	// Decrypt
	plaintext, err := gcm.Open(nil, nonce, ciphertext, nil)
	if err != nil {
		return nil, protocol.ErrDecryptionFailed
	}
	
	return plaintext, nil
}
