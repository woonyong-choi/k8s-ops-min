# ☸️ k8s-ops-min · Kyro 데이터 파이프라인

Kubernetes 운영 데이터를 수집·정규화하고 PostgreSQL 카탈로그에서 스키마·최신성·중복·리니지를 검사하는 프로젝트입니다. 팀 전체 코드와 프로젝트 종료 후의 배치·카탈로그 확장을 함께 보존합니다.

[설계 문서](docs/README.md) · [파일별 기여 근거](docs/source-and-ownership.md) · [SQL 검사](sql/checks/) · [현재 Clue 설계](https://github.com/woonyong-kr/clue)

## 로컬 실행

Python 3.13, [uv](https://docs.astral.sh/uv/getting-started/installation/), Docker Compose가 필요합니다. 새 checkout의 로컬 카탈로그를 준비합니다.

```bash
make sync
make catalog-up
make catalog-schema
make catalog-run
make catalog-verify
make catalog-test
```

PostgreSQL·MinIO·Airflow가 실행됩니다. `catalog-run`은 배치를 한 번 실행하며 `catalog-verify`는 멱등성·부분 실패·드리프트·리니지를 검사합니다. 기존 로컬 schema를 의도적으로 초기화할 때만 `make catalog-reset`을 사용합니다. 이 명령은 카탈로그 테이블과 데이터를 삭제합니다.

```bash
# 실패 조건을 직접 재현: 로컬 검증용 데이터가 변경됨
make demo-fail-source
make demo-drift
make demo-duplicate
# 조회 API: http://127.0.0.1:8000/docs
make catalog-api
```

스택 종료는 `docker compose -f docker-compose.catalog.yml stop`입니다. `make catalog-down`은 볼륨까지 제거하는 명령이므로 데이터가 필요한 환경에서는 구분해서 사용합니다.

## 구현과 설계

Kubernetes·Prometheus·Loki·Tempo → 수집 완전성·응답 상한 → 배치 → 카탈로그 → 품질 SQL → 조회 API/MCP로 이어집니다.

| 영역 | 코드와 판단 |
| --- | --- |
| [수집 계약](docs/collection-contract.md) | completed / partial / unavailable과 사유를 함께 넘겨 빈 결과를 삭제 근거로 오인하지 않도록 함 |
| [카탈로그](src/domains/datacatalog/) | 등록한 계약과 실제 관측 이력·원본·리니지를 분리 |
| [Airflow DAG](dags/catalog_reconciliation_daily.py) | 원천별 실패를 보존하고 같은 논리 날짜 재실행의 중복 적재를 방지 |
| [품질 SQL](docs/sql-quality-checks.md) | 정상 입력뿐 아니라 실제로 검출해야 할 고장 입력으로 확인 |
| [조회 API·MCP](docs/catalog-api-mcp.md) | 페이지네이션·응답 상한·토큰 신뢰 경계를 제한 |

원천 재조회 없이 보관 원본으로 backfill하며 실패한 원천만 다시 처리합니다. 성능 측정과 사각지대는 [측정 문서](docs/load-and-design-limits.md)에 있습니다. README의 고정 테스트 개수나 과거 측정값으로 현재 검증 결과를 대신하지 않습니다.

## 현재 범위와 기여

[팀 원본](https://github.com/minmings111/Kyro-jungle-final)의 전체 기능을 개인 구현으로 주장하지 않습니다. 기존 수집·정규화 기여와 종료 후 배치·카탈로그 작업의 근거는 [source-and-ownership](docs/source-and-ownership.md)에 구분되어 있습니다. 원인 판정·Draft PR·프론트엔드 전체는 팀 기능입니다.

실사용 트래픽은 검증하지 않았습니다. Airflow 정상 DAG 실행 기록은 있으나 task 재시도 소진·운영 부하는 확인하지 않았고, 실제 STS/MCP 클라이언트 연동도 미검증입니다. 조회 API가 Secret 값을 반환하지 않아도 snapshot·S3 원본에는 값이 남습니다. API의 토큰 기반 인가와 관측 데이터 보존 정책은 아직 구현 범위 밖입니다.
