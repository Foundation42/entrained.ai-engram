#!/bin/bash
# Generate self-signed SSL certificate for Engram

# Create ssl directory
mkdir -p ssl

# Generate private key and certificate
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=engram-fi-1.entrained.ai" \
    -addext "subjectAltName=DNS:engram-fi-1.entrained.ai,DNS:*.entrained.ai"

echo "✅ SSL certificate generated in ssl/ directory"
echo "   - ssl/key.pem (private key)"
echo "   - ssl/cert.pem (certificate)"
echo ""
echo "🔧 Next steps:"
echo "   1. Copy files to production server"
echo "   2. Run: docker compose -f docker-compose.prod.yml up -d"
echo "   3. Set Cloudflare SSL to 'Full' mode"
echo "   4. Test: https://engram-fi-1.entrained.ai:8443/health"