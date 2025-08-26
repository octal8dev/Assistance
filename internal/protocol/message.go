package protocol

import (
	"encoding/binary"
	"time"
)

// Message represents a Voltage protocol message
type Message struct {
	Version   uint8
	Type      uint8
	Timestamp int64
	Payload   []byte
	HMAC      []byte
}

// NewMessage creates a new message with current timestamp
func NewMessage(msgType uint8, payload []byte) *Message {
	return &Message{
		Version:   ProtocolVersion,
		Type:      msgType,
		Timestamp: time.Now().Unix(),
		Payload:   payload,
	}
}

// Marshal serializes message to bytes
func (m *Message) Marshal() []byte {
	// Calculate total size
	size := 1 + 1 + TimestampSize + 4 + len(m.Payload) + HMACSize
	buf := make([]byte, size)
	
	offset := 0
	
	// Version
	buf[offset] = m.Version
	offset++
	
	// Type
	buf[offset] = m.Type
	offset++
	
	// Timestamp
	binary.BigEndian.PutUint64(buf[offset:], uint64(m.Timestamp))
	offset += TimestampSize
	
	// Payload length
	binary.BigEndian.PutUint32(buf[offset:], uint32(len(m.Payload)))
	offset += 4
	
	// Payload
	copy(buf[offset:], m.Payload)
	offset += len(m.Payload)
	
	// HMAC
	copy(buf[offset:], m.HMAC)
	
	return buf
}

// Unmarshal deserializes message from bytes
func UnmarshalMessage(data []byte) (*Message, error) {
	if len(data) < 1+1+TimestampSize+4+HMACSize {
		return nil, ErrInvalidMessage
	}
	
	offset := 0
	msg := &Message{}
	
	// Version
	msg.Version = data[offset]
	offset++
	
	// Type
	msg.Type = data[offset]
	offset++
	
	// Timestamp
	msg.Timestamp = int64(binary.BigEndian.Uint64(data[offset:]))
	offset += TimestampSize
	
	// Payload length
	payloadLen := binary.BigEndian.Uint32(data[offset:])
	offset += 4
	
	// Validate payload length
	if len(data) < offset+int(payloadLen)+HMACSize {
		return nil, ErrInvalidMessage
	}
	
	// Payload
	msg.Payload = make([]byte, payloadLen)
	copy(msg.Payload, data[offset:offset+int(payloadLen)])
	offset += int(payloadLen)
	
	// HMAC
	msg.HMAC = make([]byte, HMACSize)
	copy(msg.HMAC, data[offset:])
	
	return msg, nil
}

// IsValid checks if message format is valid
func (m *Message) IsValid() bool {
	return m.Version == ProtocolVersion && 
		   m.Type >= MsgTypeHandshake && 
		   m.Type <= MsgTypeAck &&
		   len(m.HMAC) == HMACSize
}

// GetAge returns message age in seconds
func (m *Message) GetAge() int64 {
	return time.Now().Unix() - m.Timestamp
}
