# What is Vibe Coding?

**Vibe Coding** 실험용 레포지토리입니다.  
이 프로젝트는 **Vibe Coding(Codmex 기반 AI 개발 워크플로우)** 를 활용하여  
얼마나 빠르고 효율적으로 서버/유저 관리 시스템을 자동화 개발할 수 있는지를 검증하기 위한 목적입니다.

---

## 🚀 프로젝트 개요

**Proxmox 기반 서버 관리 + 사용자 계정 관리 시스템**을 FastAPI / Python으로 구성합니다.

AI에게 기능을 설명 → 자동으로 생성되는 코드(diff 패치) → Git 적용  
이 과정을 반복하면서, AI 개발 환경이 실제 생산성 향상에 어느 정도 기여하는지를 테스트하는 레포입니다.

---

## 📌 주요 기능

### 1. **유저(User) 관리**
- 유저 생성 / 조회 / 삭제
- 기본 프로비저닝 정책 적용
- DTO 기반의 Request/Response 규격 제공  
- 추후 OAuth2 또는 JWT 인증 확장 가능

### 2. **서버(Server) 관리**
- Proxmox API 기반 VM/LXC 생성 오케스트레이션
- 서버 생성을 위한 Saga-style 흐름 제어  
- 서버 상태 조회 / 삭제 예정  
- 향후 Billing(과금), 자원 제한 정책 연동 계획

### 3. **인프라 추상화(Infrastructure Layer)**
- Proxmox Client Stub
- Solapi(문자 인증) Stub
- In-memory Repository (→ 추후 PostgreSQL, Redis 확장 예정)

---

## 🧩 프로젝트 구조

DDD 스타일로 구성:
