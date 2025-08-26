package crypto

import (
	"crypto/ecdh"
	"crypto/rand"
	"fmt"
)

// KeyManager handles ECDH key operations
type KeyManager struct {
	privateKey *ecdh.PrivateKey
	publicKey  *ecdh.PublicKey
}

// NewKeyManager creates a new key manager
func NewKeyManager() (*KeyManager, error) {
	privateKey, publicKey, err := GenerateKeyPair()
	if err != nil {
		return nil, err
	}
	
	return &KeyManager{
		privateKey: privateKey,
		publicKey:  publicKey,
	}, nil
}

// NewKeyManagerFromPrivate creates key manager from existing private key
func NewKeyManagerFromPrivate(privateKey *ecdh.PrivateKey) *KeyManager {
	return &KeyManager{
		privateKey: privateKey,
		publicKey:  privateKey.PublicKey(),
	}
}

// GenerateKeyPair generates a new ECDH key pair
func GenerateKeyPair() (*ecdh.PrivateKey, *ecdh.PublicKey, error) {
	curve := ecdh.P256()
	privateKey, err := curve.GenerateKey(rand.Reader)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to generate private key: %w", err)
	}
	
	publicKey := privateKey.PublicKey()
	return privateKey, publicKey, nil
}

// GetPublicKey returns the public key
func (km *KeyManager) GetPublicKey() *ecdh.PublicKey {
	return km.publicKey
}

// GetPrivateKey returns the private key
func (km *KeyManager) GetPrivateKey() *ecdh.PrivateKey {
	return km.privateKey
}

// GetPublicKeyBytes returns public key as bytes
func (km *KeyManager) GetPublicKeyBytes() []byte {
	return km.publicKey.Bytes()
}

// DeriveSharedSecret derives shared secret with remote public key
func (km *KeyManager) DeriveSharedSecret(remotePublicKey *ecdh.PublicKey) ([]byte, error) {
	sharedSecret, err := km.privateKey.ECDH(remotePublicKey)
	if err != nil {
		return nil, fmt.Errorf("failed to derive shared secret: %w", err)
	}
	return sharedSecret, nil
}

// ParsePublicKey parses public key from bytes
func ParsePublicKey(data []byte) (*ecdh.PublicKey, error) {
	curve := ecdh.P256()
	publicKey, err := curve.NewPublicKey(data)
	if err != nil {
		return nil, fmt.Errorf("failed to parse public key: %w", err)
	}
	return publicKey, nil
}
