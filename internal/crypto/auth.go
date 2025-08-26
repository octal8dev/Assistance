package crypto

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/binary"

	"github.com/your-org/voltage/internal/protocol"
)

// Authenticator handles HMAC authentication
type Authenticator struct {
	key []byte
}

// NewAuthenticator creates a new authenticator
func NewAuthenticator(key []byte) *Authenticator {
	return &Authenticator{key: key}
}

// GenerateHMAC generates HMAC for a message
func (a *Authenticator) GenerateHMAC(msg *protocol.Message) []byte {
	h := hmac.New(sha256.New, a.key)
	
	// Write message data (without HMAC)
	h.Write([]byte{msg.Version, msg.Type})
	
	timestampBytes := make([]byte, 8)
	binary.BigEndian.PutUint64(timestampBytes, uint64(msg.Timestamp))
	h.Write(timestampBytes)
	
	h.Write(msg.Payload)
	
	return h.Sum(nil)
}

// VerifyHMAC verifies message HMAC
func (a *Authenticator) VerifyHMAC(msg *protocol.Message) bool {
	expected := a.GenerateHMAC(msg)
	return hmac.Equal(expected, msg.HMAC)
}

// DeriveKey derives a key from shared secret using HKDF-like approach
func DeriveKey(sharedSecret, info []byte) []byte {
	h := hmac.New(sha256.New, sharedSecret)
	h.Write(info)
	return h.Sum(nil)
}
