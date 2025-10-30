#!/bin/bash
# Direct agent execution on production (no wrapper, no local saving)

echo "================================================================================"
echo "Running Test Engineer Agent DIRECTLY on production"
echo "================================================================================"
echo ""
echo "Mode: Direct SSH (results stay on production)"
echo ""

ssh -i /c/Users/Андрей/.ssh/id_rsa -o StrictHostKeyChecking=no root@5.35.88.251 \
  "cd /var/GrantService && \
   export PGHOST=localhost && \
   export PGPORT=5434 && \
   export PGDATABASE=grantservice && \
   export PGUSER=grantservice && \
   export PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q' && \
   python3 tester/agent.py --mock-websearch"
