# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Build stage
FROM golang:1.26-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum* ./

# Download dependencies
RUN go mod download

# Copy source code
COPY main.go ./
COPY agent/ ./agent/

# Build the binary
RUN CGO_ENABLED=0 GOOS=linux go build -o /agent .

{%- if cookiecutter.agent_gateway %}

# Install the Agent Gateway root CA passed by the platform.
# Based on https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/agent-gateway-runtime-deploy#configure-byoc
ARG AGENT_GATEWAY_ROOT_CERTIFICATES
RUN if [ -n "$AGENT_GATEWAY_ROOT_CERTIFICATES" ]; then \
      mkdir -p /usr/local/share/ca-certificates; \
      printf "%b" "$AGENT_GATEWAY_ROOT_CERTIFICATES" \
        | awk 'BEGIN {c=0} /BEGIN CERTIFICATE/ {c++} c > 0 { print > "/usr/local/share/ca-certificates/agw-" c ".crt" }'; \
      update-ca-certificates; \
    fi
{%- endif %}

# Runtime stage
FROM gcr.io/distroless/static-debian12

COPY --from=builder /agent /agent

ARG COMMIT_SHA=""
ENV COMMIT_SHA=${COMMIT_SHA}

{%- if cookiecutter.agent_gateway %}

# If Agent Gateway root CA was provided, configure SSL/TLS trust paths.
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/agent-gateway-ca-certificates.crt
ARG AGENT_GATEWAY_ROOT_CERTIFICATES
ENV SSL_CERT_FILE=${AGENT_GATEWAY_ROOT_CERTIFICATES:+/etc/ssl/certs/agent-gateway-ca-certificates.crt}
{%- endif %}

EXPOSE 8080

# Cloud Run sets PORT env var which ADK launcher reads automatically
# Supports REST API, A2A protocol, and Web UI
# API endpoints: /api/run_sse, /api/apps/...
# A2A endpoint: /a2a/invoke (JSON-RPC)
# Agent card: /.well-known/agent-card.json
# Web UI: /ui/ (requires IAP for authenticated access)
{%- if cookiecutter.deployment_target == 'gke' %}
# GKE does not inject a PORT env var, so bind the ADK launcher to 8080 explicitly.
ENTRYPOINT ["/agent", "web", "--port", "8080", "api", "a2a", "webui"]
{%- else %}
ENTRYPOINT ["/agent", "web", "api", "a2a", "webui"]
{%- endif %}
