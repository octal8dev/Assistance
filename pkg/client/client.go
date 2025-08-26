package client

import (
	"crypto/ecdh"
	"fmt"
	"time"

	"github.com/klauspost/compress/zstd"
	"github.com/your-org/voltage/internal/crypto"
	"github.com/your-org/voltage/internal/handshake"
	"github.com/your-org/voltage/internal/protocol"
)

// Client represents a Voltage protocol client
type Client struct {
	keyManager    *crypto.KeyManager
	encryptor     *crypto.Encryptor
	auth          *crypto.Authenticator
	handshaker    *handshake.Manager
	compressor    *zstd.Encoder
	decompressor  *zstd.Decoder
	
	// Connection state
	sessionKey    []byte
	connected     bool
	useCompression bool
}

// Config holds client configuration
type Config struct {
	PrivateKey        []byte
	EnableCompression bool
}

// New creates a new Voltage client
func New(config Config) (*Client, error) {
	var keyManager *crypto.KeyManager
	var err error
	
	if config.PrivateKey != nil {
		// Parse existing private key
		curve := ecdh.P256()
		privateKey, err := curve.NewPrivateKey(config.PrivateKey)
		if err != nil {
			return nil, fmt.Errorf("failed to parse private key: %w", err)
		}
		keyManager = crypto.NewKeyManagerFromPrivate(privateKey)
	} else {
		// Generate new key pair
		keyManager, err = crypto.NewKeyManager()
		if err != nil {
			return nil, fmt.Errorf("failed to create key manager: %w", err)
		}
	}
	
	client := &Client{
		keyManager:     keyManager,
		handshaker:     handshake.NewManager(keyManager),
		useCompression: config.EnableCompression,
	}
	
	// Initialize compressor if enabled
	if config.EnableCompression {
		encoder, err := zstd.NewWriter(nil, zstd.WithEncoderLevel(zstd.SpeedFastest))
		if err != nil {
			return nil, fmt.Errorf("failed to create compressor: %w", err)
		}
		client.compressor = encoder
		
		decoder, err := zstd.NewReader(nil)
		if err != nil {
			return nil, fmt.Errorf("failed to create decompressor: %w", err)
		}
		client.decompressor = decoder
	}
	
	return client, nil
}

// GetPublicKey returns client's public key bytes
func (c *Client) GetPublicKey() []byte {
	return c.keyManager.GetPublicKeyBytes()
}

// StartHandshake initiates handshake process
func (c *Client) StartHandshake() (*protocol.Message, error) {
	return c.handshaker.CreateHandshakeMessage()
}

// ProcessHandshake processes handshake message and establishes session
func (c *Client) ProcessHandshake(msg *protocol.Message) (*protocol.Message, error) {
	sessionKey, err := c.handshaker.ProcessHandshakeMessage(msg)
	if err != nil {
		return nil, err
	}
	
	// Setup encryption and authentication
	if err := c.setupSession(sessionKey); err != nil {
		return nil, err
	}
	
	// Create handshake response
	return c.handshaker.CreateHandshakeResponse()
}

// CompleteHandshake completes handshake process
func (c *Client) CompleteHandshake(msg *protocol.Message) error {
	sessionKey, err := c.handshaker.ProcessHandshakeResponse(msg)
	if err != nil {
		return err
	}
	
	// Setup encryption and authentication
	return c.setupSession(sessionKey)
}

// setupSession initializes session with given key
func (c *Client) setupSession(sessionKey []byte) error {
	c.sessionKey = sessionKey
	
	// Setup encryptor
	encryptor, err := crypto.NewEncryptor(sessionKey)
	if err != nil {
		return fmt.Errorf("failed to create encryptor: %w", err)
	}
	c.encryptor = encryptor
	
	// Setup authenticator
	c.auth = crypto.NewAuthenticator(sessionKey)
	
	c.connected = true
	return nil
}

// Encrypt encrypts data and creates message
func (c *Client) Encrypt(data []byte) (*protocol.Message, error) {
	if !c.connected {
		return nil, protocol.ErrNotConnected
	}
	
	// Compress data if enabled
	payload := data
	if c.useCompression && c.compressor != nil {
		payload = c.compressor.EncodeAll(data, nil)
	}
	
	// Encrypt payload
	encryptedPayload, err := c.encryptor.Encrypt(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to encrypt: %w", err)
	}
	
	// Create message
	msg := protocol.NewMessage(protocol.MsgTypeData, encryptedPayload)
	
	// Generate HMAC
	msg.HMAC = c.auth.GenerateHMAC(msg)
	
	return msg, nil
}

// Decrypt decrypts message data
func (c *Client) Decrypt(msg *protocol.Message) ([]byte, error) {
	if !c.connected {
		return nil, protocol.ErrNotConnected
	}
	
	// Verify HMAC
	if !c.auth.VerifyHMAC(msg) {
		return nil, protocol.ErrInvalidSignature
	}
	
	// Verify timestamp (allow 5 minute skew)
	if msg.GetAge() > 300 {
		return nil, protocol.ErrInvalidTimestamp
	}
	
	// Decrypt payload
	decryptedPayload, err := c.encryptor.Decrypt(msg.Payload)
	if err != nil {
		return nil, fmt.Errorf("failed to decrypt: %w", err)
	}
	
	// Decompress if needed
	if c.useCompression && c.decompressor != nil {
		decompressed, err := c.decompressor.DecodeAll(decryptedPayload, nil)
		if err != nil {
			return nil, fmt.Errorf("failed to decompress: %w", err)
		}
		return decompressed, nil
	}
	
	return decryptedPayload, nil
}

// CreateHeartbeat creates a heartbeat message
func (c *Client) CreateHeartbeat() (*protocol.Message, error) {
	msg := protocol.NewMessage(protocol.MsgTypeHeartbeat, []byte("ping"))
	
	if c.connected {
		msg.HMAC = c.auth.GenerateHMAC(msg)
	}
	
	return msg, nil
}

// IsConnected returns connection status
func (c *Client) IsConnected() bool {
	return c.connected
}

// Close closes the client and cleans up resources
func (c *Client) Close() error {
	c.connected = false
	
	if c.compressor != nil {
		c.compressor.Close()
	}
	
	if c.decompressor != nil {
		c.decompressor.Close()
	}
	
	return nil
}
