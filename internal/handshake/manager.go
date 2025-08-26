package handshake

import (
	"crypto/ecdh"
	"crypto/sha256"
	"fmt"
	"time"

	"github.com/your-org/voltage/internal/crypto"
	"github.com/your-org/voltage/internal/protocol"
)

// Manager handles handshake operations
type Manager struct {
	keyManager *crypto.KeyManager
	auth       *crypto.Authenticator
}

// NewManager creates a new handshake manager
func NewManager(keyManager *crypto.KeyManager) *Manager {
	// Use temporary key for handshake authentication
	tempKey := sha256.Sum256([]byte("voltage-handshake"))
	auth := crypto.NewAuthenticator(tempKey[:])
	
	return &Manager{
		keyManager: keyManager,
		auth:       auth,
	}
}

// CreateHandshakeMessage creates a handshake message
func (m *Manager) CreateHandshakeMessage() (*protocol.Message, error) {
	// Send public key as payload
	publicKeyBytes := m.keyManager.GetPublicKeyBytes()
	
	msg := protocol.NewMessage(protocol.MsgTypeHandshake, publicKeyBytes)
	
	// Generate HMAC
	msg.HMAC = m.auth.GenerateHMAC(msg)
	
	return msg, nil
}

// ProcessHandshakeMessage processes incoming handshake message
func (m *Manager) ProcessHandshakeMessage(msg *protocol.Message) ([]byte, error) {
	if msg.Type != protocol.MsgTypeHandshake {
		return nil, fmt.Errorf("expected handshake message, got type %d", msg.Type)
	}
	
	// Verify HMAC
	if !m.auth.VerifyHMAC(msg) {
		return nil, protocol.ErrInvalidSignature
	}
	
	// Parse remote public key
	remotePublicKey, err := crypto.ParsePublicKey(msg.Payload)
	if err != nil {
		return nil, fmt.Errorf("failed to parse remote public key: %w", err)
	}
	
	// Generate shared secret
	sharedSecret, err := m.keyManager.DeriveSharedSecret(remotePublicKey)
	if err != nil {
		return nil, fmt.Errorf("failed to derive shared secret: %w", err)
	}
	
	// Derive session key
	sessionKey := crypto.DeriveKey(sharedSecret, []byte("voltage-session"))
	
	return sessionKey, nil
}

// CreateHandshakeResponse creates a handshake response message
func (m *Manager) CreateHandshakeResponse() (*protocol.Message, error) {
	// Send public key as payload
	publicKeyBytes := m.keyManager.GetPublicKeyBytes()
	
	msg := protocol.NewMessage(protocol.MsgTypeAck, publicKeyBytes)
	
	// Generate HMAC
	msg.HMAC = m.auth.GenerateHMAC(msg)
	
	return msg, nil
}

// ProcessHandshakeResponse processes handshake response
func (m *Manager) ProcessHandshakeResponse(msg *protocol.Message) ([]byte, error) {
	if msg.Type != protocol.MsgTypeAck {
		return nil, fmt.Errorf("expected handshake response, got type %d", msg.Type)
	}
	
	// Verify HMAC
	if !m.auth.VerifyHMAC(msg) {
		return nil, protocol.ErrInvalidSignature
	}
	
	// Parse remote public key
	remotePublicKey, err := crypto.ParsePublicKey(msg.Payload)
	if err != nil {
		return nil, fmt.Errorf("failed to parse remote public key: %w", err)
	}
	
	// Generate shared secret
	sharedSecret, err := m.keyManager.DeriveSharedSecret(remotePublicKey)
	if err != nil {
		return nil, fmt.Errorf("failed to derive shared secret: %w", err)
	}
	
	// Derive session key
	sessionKey := crypto.DeriveKey(sharedSecret, []byte("voltage-session"))
	
	return sessionKey, nil
}
