package protocol

import "errors"

const (
	// Protocol constants
	ProtocolVersion = 0x01
	
	// Crypto constants
	NonceSize     = 12  // GCM nonce size
	TagSize       = 16  // GCM tag size
	HMACSize      = 32  // SHA256 HMAC size
	KeySize       = 32  // AES-256 key size
	TimestampSize = 8   // Unix timestamp size
	
	// Message types
	MsgTypeHandshake = 0x01
	MsgTypeData      = 0x02
	MsgTypeHeartbeat = 0x03
	MsgTypeError     = 0x04
	MsgTypeAck       = 0x05
)

var (
	ErrInvalidMessage   = errors.New("invalid message format")
	ErrInvalidSignature = errors.New("invalid message signature")
	ErrInvalidTimestamp = errors.New("invalid timestamp")
	ErrEncryptionFailed = errors.New("encryption failed")
	ErrDecryptionFailed = errors.New("decryption failed")
	ErrNoSessionKey     = errors.New("no session key available")
	ErrNotConnected     = errors.New("not connected")
	ErrHandshakeFailed  = errors.New("handshake failed")
)
