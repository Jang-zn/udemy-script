#!/usr/bin/env python3
"""
대용량 transcript 파일을 읽어서 간결한 학습자료를 생성하는 스크립트
"""

def read_large_file(file_path):
    """파일을 읽어서 내용을 반환"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def extract_key_sections(content, section_name):
    """핵심 섹션을 추출하여 요약"""
    lines = content.split('\n')

    # 섹션 헤더 찾기
    sections = []
    current_section = None
    current_content = []

    for line in lines:
        if line.startswith('## '):
            if current_section:
                sections.append({
                    'title': current_section,
                    'content': '\n'.join(current_content)
                })
            current_section = line.replace('## ', '').strip()
            current_content = []
        elif line.strip():
            current_content.append(line)

    if current_section:
        sections.append({
            'title': current_section,
            'content': '\n'.join(current_content)
        })

    return sections

def create_section_19_material(content):
    """Section 19: RediSearch 학습자료 작성"""
    material = """# Section 19: RediSearch로 데이터 쿼리하기

## 학습 목표
- Redis 모듈의 개념과 필요성 이해
- RediSearch 모듈을 사용한 전문 검색 구현
- FT.CREATE, FT.SEARCH 등 RediSearch 명령어 활용

## 핵심 개념

### 1. Redis 모듈이란?
- Redis의 기본 기능을 확장하는 별도 프로그램
- 새로운 데이터 구조와 명령어를 추가
- 주요 모듈: RedisJSON, RediSearch, RedisGraph, RedisTimeSeries

### 2. Redis Stack
- 여러 모듈이 미리 설치된 Redis 배포판
- 추가 설정 없이 바로 사용 가능
- 포함 모듈: RediSearch, RedisJSON, RedisGraph, RedisTimeSeries, RedisBloom

### 3. RediSearch 핵심 기능
- **전문 텍스트 검색**: 키워드 기반 검색 지원
- **필터링**: 여러 조건을 조합한 복잡한 쿼리
- **정렬**: 다양한 필드 기준 정렬
- **집계**: 검색 결과에 대한 통계 및 집계

## 주요 명령어

### 인덱스 생성
```redis
FT.CREATE idx:items
  ON HASH PREFIX 1 items:
  SCHEMA
    name TEXT SORTABLE
    price NUMERIC SORTABLE
    description TEXT
    category TAG
```

### 검색 수행
```redis
# 기본 텍스트 검색
FT.SEARCH idx:items "laptop"

# 필터링과 정렬
FT.SEARCH idx:items "*"
  FILTER price 100 500
  SORTBY price ASC
  LIMIT 0 10

# 태그 필터
FT.SEARCH idx:items "@category:{electronics}"

# 복합 쿼리
FT.SEARCH idx:items "@name:(laptop computer) @category:{electronics}"
  FILTER price 0 1000
  SORTBY price DESC
```

### 인덱스 관리
```redis
# 인덱스 정보 확인
FT.INFO idx:items

# 인덱스 삭제
FT.DROPINDEX idx:items

# 인덱스 목록
FT._LIST
```

## 필드 타입

### TEXT
- 전문 텍스트 검색용
- 토큰화 및 형태소 분석 지원
- SORTABLE 옵션으로 정렬 가능

### NUMERIC
- 숫자 필드
- 범위 검색 및 정렬 지원
- 가격, 평점, 수량 등에 사용

### TAG
- 카테고리, 태그 등에 사용
- 정확한 매칭만 지원
- 구분자로 여러 값 저장 가능

### GEO
- 지리적 좌표 저장
- 위치 기반 검색 지원

## 실전 활용 패턴

### 1. 전자상거래 상품 검색
```redis
# 인덱스 생성
FT.CREATE idx:products
  ON HASH PREFIX 1 products:
  SCHEMA
    name TEXT SORTABLE
    price NUMERIC SORTABLE
    brand TAG
    rating NUMERIC SORTABLE

# 검색: "스마트폰" 키워드, 10만원~50만원, 평점 4.0 이상
FT.SEARCH idx:products "스마트폰"
  FILTER price 100000 500000
  FILTER rating 4.0 5.0
  SORTBY rating DESC
```

### 2. 자동완성
```redis
# 접두사 검색
FT.SEARCH idx:products "lap*"
```

### 3. 페이지네이션
```redis
# 페이지 1 (0~9)
FT.SEARCH idx:products "*" LIMIT 0 10

# 페이지 2 (10~19)
FT.SEARCH idx:products "*" LIMIT 10 10
```

## 성능 최적화 팁

1. **필요한 필드만 인덱싱**: 모든 필드를 인덱싱하면 성능 저하
2. **SORTABLE 신중히 사용**: 메모리 사용량 증가
3. **적절한 PREFIX 설정**: 불필요한 키 스캔 방지
4. **LIMIT 사용**: 결과 수 제한으로 성능 향상

## 주의사항

1. **모듈 사용 제약**
   - AWS ElastiCache, Google Cloud Memorystore는 모듈 미지원
   - 직접 운영하거나 Redis Enterprise Cloud 사용 필요

2. **인덱스 관리**
   - 인덱스는 메모리 소비
   - 불필요한 인덱스는 삭제

3. **검색 쿼리 복잡도**
   - 과도하게 복잡한 쿼리는 성능 저하
   - 적절한 인덱스 설계 필요

## 요약

RediSearch는 Redis에 강력한 검색 기능을 추가하는 모듈입니다. 전문 텍스트 검색, 필터링, 정렬 등을 지원하여 전자상거래, 콘텐츠 관리 등 다양한 애플리케이션에서 활용할 수 있습니다. Redis Stack을 사용하면 별도 설정 없이 바로 사용할 수 있습니다.
"""
    return material

def create_section_20_material(content):
    """Section 20: 검색 구현 학습자료 작성"""
    material = """# Section 20: 검색 구현하기

## 학습 목표
- RediSearch를 활용한 실전 검색 기능 구현
- 복잡한 검색 쿼리 작성 및 최적화
- 페이지네이션, 필터링, 정렬 통합 구현

## 핵심 구현 패턴

### 1. 검색 API 구조
```javascript
// 검색 파라미터
const searchParams = {
  query: 'laptop',           // 검색어
  category: 'electronics',   // 카테고리 필터
  minPrice: 100,            // 최소 가격
  maxPrice: 1000,           // 최대 가격
  sortBy: 'price',          // 정렬 기준
  sortOrder: 'ASC',         // 정렬 방향
  page: 1,                  // 페이지 번호
  pageSize: 20              // 페이지 크기
}

async function searchProducts(params) {
  // RediSearch 쿼리 빌드
  const query = buildSearchQuery(params);

  // 검색 실행
  const results = await client.ft.search('idx:products', query, {
    LIMIT: {
      from: (params.page - 1) * params.pageSize,
      size: params.pageSize
    }
  });

  return {
    total: results.total,
    items: results.documents,
    page: params.page,
    pageSize: params.pageSize
  };
}
```

### 2. 쿼리 빌더
```javascript
function buildSearchQuery(params) {
  const conditions = [];

  // 텍스트 검색
  if (params.query) {
    conditions.push(`@name:(${params.query})`);
  }

  // 카테고리 필터
  if (params.category) {
    conditions.push(`@category:{${params.category}}`);
  }

  // 가격 범위
  if (params.minPrice || params.maxPrice) {
    const min = params.minPrice || 0;
    const max = params.maxPrice || '+inf';
    conditions.push(`@price:[${min} ${max}]`);
  }

  // 조건 결합
  return conditions.length > 0 ? conditions.join(' ') : '*';
}
```

### 3. 다중 필터 검색
```javascript
// 복잡한 필터 조합
FT.SEARCH idx:products
  "@name:(laptop computer) @brand:{apple|dell|hp} @category:{electronics}"
  FILTER price 500 2000
  FILTER rating 4.0 5.0
  SORTBY rating DESC
  LIMIT 0 20
```

## 실전 시나리오

### 시나리오 1: 전자상거래 상품 검색
```javascript
// 요구사항:
// - 키워드 검색
// - 브랜드 필터 (다중 선택)
// - 가격 범위
// - 평점 필터
// - 재고 있는 상품만
// - 가격순/평점순 정렬

const searchConfig = {
  index: 'idx:products',
  query: '@name:(smartphone) @brand:{samsung|apple} @inStock:{true}',
  filter: [
    { field: 'price', min: 300, max: 1500 },
    { field: 'rating', min: 4.0, max: 5.0 }
  ],
  sort: { field: 'price', order: 'ASC' },
  pagination: { page: 1, size: 20 }
};
```

### 시나리오 2: 자동완성
```javascript
async function autocomplete(prefix) {
  // 접두사 검색
  const results = await client.ft.search(
    'idx:products',
    `@name:(${prefix}*)`,
    { LIMIT: { from: 0, size: 10 } }
  );

  return results.documents.map(doc => ({
    id: doc.id,
    name: doc.value.name,
    price: doc.value.price
  }));
}

// 사용 예
autocomplete('lap');  // laptop, lapis, etc.
```

### 시나리오 3: 패싯 검색
```javascript
// 검색 결과와 함께 필터 옵션 제공
async function searchWithFacets(query) {
  // 1. 기본 검색
  const results = await client.ft.search('idx:products', query);

  // 2. 집계로 카테고리별 개수 계산
  const categories = await client.ft.aggregate('idx:products', query, {
    GROUPBY: '@category',
    REDUCE: 'COUNT 0 AS count'
  });

  // 3. 브랜드별 개수
  const brands = await client.ft.aggregate('idx:products', query, {
    GROUPBY: '@brand',
    REDUCE: 'COUNT 0 AS count'
  });

  return {
    results: results.documents,
    facets: {
      categories,
      brands
    }
  };
}
```

### 시나리오 4: 지리적 검색
```javascript
// 위치 기반 상점 검색
FT.CREATE idx:stores
  ON HASH PREFIX 1 stores:
  SCHEMA
    name TEXT
    location GEO
    rating NUMERIC SORTABLE

// 반경 5km 내 검색
FT.SEARCH idx:stores
  "@location:[127.0276 37.4979 5 km]"
  SORTBY rating DESC
```

## 성능 최적화

### 1. 인덱스 설계
```redis
# 좋은 예: 필요한 필드만 인덱싱
FT.CREATE idx:products
  ON HASH PREFIX 1 products:
  SCHEMA
    name TEXT SORTABLE
    price NUMERIC SORTABLE
    brand TAG
    category TAG

# 나쁜 예: 모든 필드를 SORTABLE로
# -> 메모리 사용량 증가
```

### 2. 쿼리 최적화
```javascript
// 좋은 예: 구체적인 조건
FT.SEARCH idx:products "@name:(laptop) @category:{electronics}" LIMIT 0 20

// 나쁜 예: 와일드카드만 사용
FT.SEARCH idx:products "*" LIMIT 0 1000  // 너무 많은 결과
```

### 3. 결과 제한
```javascript
// 항상 LIMIT 사용
const MAX_PAGE_SIZE = 100;

function search(params) {
  const pageSize = Math.min(params.pageSize || 20, MAX_PAGE_SIZE);
  // ...
}
```

### 4. 캐싱 전략
```javascript
// 인기 검색어는 캐시
const searchCache = new Map();

async function cachedSearch(query, params) {
  const cacheKey = JSON.stringify({ query, params });

  if (searchCache.has(cacheKey)) {
    return searchCache.get(cacheKey);
  }

  const results = await search(query, params);
  searchCache.set(cacheKey, results);

  // 5분 후 만료
  setTimeout(() => searchCache.delete(cacheKey), 5 * 60 * 1000);

  return results;
}
```

## 사용자 경험 개선

### 1. 검색어 하이라이팅
```javascript
// HIGHLIGHT 옵션 사용
FT.SEARCH idx:products "laptop"
  HIGHLIGHT FIELDS 2 name description
  TAGS "<mark>" "</mark>"
```

### 2. Did You Mean (검색어 제안)
```javascript
// 오타 허용 검색
FT.SEARCH idx:products "%laptpo%"  // 편집 거리 1 허용
```

### 3. 정렬 옵션 제공
```javascript
const sortOptions = [
  { label: '관련도순', value: 'relevance' },
  { label: '가격 낮은순', value: 'price_asc' },
  { label: '가격 높은순', value: 'price_desc' },
  { label: '평점순', value: 'rating_desc' },
  { label: '최신순', value: 'created_desc' }
];
```

## 에러 처리

```javascript
async function safeSearch(query, params) {
  try {
    return await client.ft.search('idx:products', query, params);
  } catch (error) {
    if (error.message.includes('no such index')) {
      // 인덱스가 없으면 생성
      await createIndex();
      return await client.ft.search('idx:products', query, params);
    }

    if (error.message.includes('syntax error')) {
      // 쿼리 문법 오류 - 기본 검색으로 대체
      return await client.ft.search('idx:products', '*', params);
    }

    throw error;
  }
}
```

## 요약

RediSearch를 활용한 검색 구현은 복잡한 필터링, 정렬, 페이지네이션을 효율적으로 처리할 수 있습니다. 쿼리 빌더 패턴으로 동적 검색을 구현하고, 적절한 인덱스 설계와 캐싱으로 성능을 최적화하며, 사용자 경험을 개선하는 다양한 기능을 추가할 수 있습니다.
"""
    return material

def create_section_21_material(content):
    """Section 21: Streams 학습자료 작성"""
    material = """# Section 21: 스트림을 통한 서비스 통신

## 학습 목표
- Redis Streams의 개념과 활용 사례 이해
- XADD, XREAD, XGROUP 등 Streams 명령어 마스터
- 이벤트 기반 아키텍처 구현

## Redis Streams란?

### 핵심 개념
- **로그 기반 데이터 구조**: 시간순으로 정렬된 메시지 저장
- **메시지 브로커 기능**: 생산자-소비자 패턴 지원
- **Consumer Group**: 여러 소비자가 병렬로 메시지 처리
- **영속성**: 메시지가 Redis에 저장되어 재처리 가능

### Kafka/RabbitMQ와의 비교
- **장점**:
  - 설정 간단
  - Redis 인프라 재사용
  - 빠른 성능
- **단점**:
  - 전문 메시지 브로커보다 기능 제한적
  - 클러스터링 기능 상대적으로 약함

## 주요 명령어

### 1. 메시지 추가 (Producer)
```redis
# 자동 ID 생성
XADD orders:stream *
  orderId "12345"
  userId "user:100"
  amount "59.99"
  status "pending"

# 결과: "1234567890123-0" (타임스탬프-시퀀스)

# 특정 ID 지정
XADD orders:stream 1234567890123-0
  orderId "12346"
  status "completed"

# 최대 길이 제한
XADD orders:stream MAXLEN ~ 1000 *
  orderId "12347"
  status "pending"
```

### 2. 메시지 읽기 (Consumer)
```redis
# 모든 메시지 읽기
XREAD STREAMS orders:stream 0

# 새 메시지만 읽기 (블로킹)
XREAD BLOCK 0 STREAMS orders:stream $

# 타임아웃 설정 (5초)
XREAD BLOCK 5000 STREAMS orders:stream $

# 여러 스트림 읽기
XREAD STREAMS orders:stream notifications:stream $ $

# 특정 ID 이후 읽기
XREAD STREAMS orders:stream 1234567890123-0
```

### 3. Consumer Groups
```redis
# 그룹 생성
XGROUP CREATE orders:stream order-processors $ MKSTREAM

# 그룹에서 읽기
XREADGROUP GROUP order-processors consumer1
  BLOCK 0
  STREAMS orders:stream >

# 메시지 확인 (ACK)
XACK orders:stream order-processors 1234567890123-0

# 미확인 메시지 확인
XPENDING orders:stream order-processors

# 메시지 재할당
XCLAIM orders:stream order-processors consumer2 60000
  1234567890123-0
```

### 4. 스트림 관리
```redis
# 스트림 정보
XINFO STREAM orders:stream

# 그룹 정보
XINFO GROUPS orders:stream

# 소비자 정보
XINFO CONSUMERS orders:stream order-processors

# 스트림 길이
XLEN orders:stream

# 메시지 삭제
XDEL orders:stream 1234567890123-0

# 메시지 트림
XTRIM orders:stream MAXLEN 1000
```

## 실전 활용 패턴

### 패턴 1: 주문 처리 시스템
```javascript
// Producer: 주문 생성 서비스
async function createOrder(orderData) {
  const orderId = generateOrderId();

  // 1. 주문 데이터 저장
  await client.hSet(`order:${orderId}`, orderData);

  // 2. 이벤트 발행
  await client.xAdd('orders:stream', '*', {
    event: 'order.created',
    orderId: orderId,
    userId: orderData.userId,
    amount: orderData.amount,
    timestamp: Date.now()
  });

  return orderId;
}

// Consumer: 결제 처리 서비스
async function processPayments() {
  const group = 'payment-processors';
  const consumer = 'processor-1';

  // Consumer Group 생성
  try {
    await client.xGroupCreate('orders:stream', group, '$', {
      MKSTREAM: true
    });
  } catch (err) {
    // 그룹이 이미 존재
  }

  while (true) {
    // 메시지 읽기
    const messages = await client.xReadGroup(
      group,
      consumer,
      [{ key: 'orders:stream', id: '>' }],
      { BLOCK: 5000, COUNT: 10 }
    );

    if (!messages || messages.length === 0) continue;

    for (const [stream, entries] of messages) {
      for (const { id, message } of entries) {
        try {
          // 결제 처리
          await processPayment(message);

          // ACK
          await client.xAck('orders:stream', group, id);

          // 다음 이벤트 발행
          await client.xAdd('orders:stream', '*', {
            event: 'payment.processed',
            orderId: message.orderId,
            status: 'paid'
          });
        } catch (error) {
          console.error('Payment failed:', error);
          // 에러는 ACK하지 않음 -> 재처리 대상
        }
      }
    }
  }
}
```

### 패턴 2: 실시간 알림 시스템
```javascript
// 알림 발행
async function sendNotification(userId, message) {
  await client.xAdd('notifications:stream', '*', {
    userId: userId,
    type: 'push',
    title: message.title,
    body: message.body,
    timestamp: Date.now()
  });
}

// 사용자별 알림 구독 (WebSocket 서버)
async function subscribeUserNotifications(userId, socket) {
  let lastId = '$';

  while (socket.connected) {
    const messages = await client.xRead(
      [{ key: 'notifications:stream', id: lastId }],
      { BLOCK: 1000 }
    );

    if (messages) {
      for (const [stream, entries] of messages) {
        for (const { id, message } of entries) {
          if (message.userId === userId) {
            socket.emit('notification', message);
          }
          lastId = id;
        }
      }
    }
  }
}
```

### 패턴 3: 이벤트 소싱
```javascript
// 이벤트 저장
async function recordEvent(aggregateId, eventType, data) {
  await client.xAdd(`events:${aggregateId}`, '*', {
    type: eventType,
    data: JSON.stringify(data),
    timestamp: Date.now()
  });
}

// 이벤트 재생으로 상태 복원
async function rebuildState(aggregateId) {
  const events = await client.xRange(`events:${aggregateId}`, '-', '+');

  let state = {};
  for (const { message } of events) {
    state = applyEvent(state, message.type, JSON.parse(message.data));
  }

  return state;
}

// 사용 예: 장바구니 이벤트 소싱
await recordEvent('cart:user123', 'item.added', { itemId: 'product1', quantity: 1 });
await recordEvent('cart:user123', 'item.removed', { itemId: 'product2' });
await recordEvent('cart:user123', 'checkout.completed', { orderId: 'order456' });

const cartState = await rebuildState('cart:user123');
```

### 패턴 4: 분산 작업 큐
```javascript
// 작업 생산자
async function queueTask(taskType, taskData) {
  await client.xAdd('tasks:stream', '*', {
    type: taskType,
    data: JSON.stringify(taskData),
    priority: taskData.priority || 'normal',
    createdAt: Date.now()
  });
}

// 워커 (여러 인스턴스 실행 가능)
async function worker(workerId) {
  const group = 'task-workers';

  while (true) {
    const messages = await client.xReadGroup(
      group,
      workerId,
      [{ key: 'tasks:stream', id: '>' }],
      { BLOCK: 5000, COUNT: 1 }
    );

    if (messages) {
      for (const [stream, entries] of messages) {
        for (const { id, message } of entries) {
          try {
            // 작업 실행
            await executeTask(message.type, JSON.parse(message.data));

            // 완료 확인
            await client.xAck('tasks:stream', group, id);
          } catch (error) {
            console.error(`Task ${id} failed:`, error);
            // 재시도 로직 추가 가능
          }
        }
      }
    }
  }
}
```

## 고급 기능

### 1. 메시지 재처리 (Dead Letter)
```javascript
async function handlePendingMessages() {
  const group = 'order-processors';
  const idleTime = 60000; // 1분

  // 오래된 미확인 메시지 찾기
  const pending = await client.xPending('orders:stream', group);

  if (pending.pending > 0) {
    const messages = await client.xPendingRange(
      'orders:stream',
      group,
      '-', '+',
      10
    );

    for (const msg of messages) {
      if (msg.millisecondsSinceLastDelivery > idleTime) {
        // Dead Letter Queue로 이동
        await client.xAdd('orders:dlq', '*', {
          originalId: msg.id,
          consumer: msg.consumer,
          deliveryCount: msg.deliveryCount
        });

        // 원본 메시지 ACK
        await client.xAck('orders:stream', group, msg.id);
      }
    }
  }
}
```

### 2. 스트림 파티셔닝
```javascript
// 사용자 ID 기반 파티셔닝
function getStreamName(userId) {
  const partition = parseInt(userId) % 4; // 4개 파티션
  return `orders:stream:${partition}`;
}

async function addOrder(userId, orderData) {
  const stream = getStreamName(userId);
  await client.xAdd(stream, '*', {
    userId,
    ...orderData
  });
}
```

### 3. 스트림 백업
```javascript
async function backupStream(streamName, outputFile) {
  const messages = await client.xRange(streamName, '-', '+');

  const backup = messages.map(({ id, message }) => ({
    id,
    data: message
  }));

  await fs.writeFile(outputFile, JSON.stringify(backup));
}
```

## 모니터링 및 디버깅

```javascript
// 스트림 상태 모니터링
async function monitorStream(streamName) {
  const info = await client.xInfoStream(streamName);

  console.log({
    length: info.length,
    firstEntry: info.firstEntry,
    lastEntry: info.lastEntry,
    groups: info.groups
  });

  // 그룹별 lag 확인
  const groups = await client.xInfoGroups(streamName);
  for (const group of groups) {
    console.log({
      name: group.name,
      consumers: group.consumers,
      pending: group.pending,
      lastDeliveredId: group.lastDeliveredId
    });
  }
}
```

## 성능 최적화

1. **배치 처리**: COUNT 옵션으로 여러 메시지 한번에 처리
2. **적절한 MAXLEN**: 오래된 메시지 자동 삭제로 메모리 관리
3. **Consumer Group 활용**: 병렬 처리로 처리량 증대
4. **블로킹 시간 조정**: BLOCK 시간을 적절히 설정

## 요약

Redis Streams는 이벤트 기반 아키텍처를 구현하는 강력한 도구입니다. 메시지 브로커, 작업 큐, 이벤트 소싱 등 다양한 패턴을 지원하며, Consumer Groups를 통한 병렬 처리와 장애 복구 기능을 제공합니다. 간단한 설정으로 확장 가능한 비동기 시스템을 구축할 수 있습니다.
"""
    return material

def main():
    base_path = "/Users/jang/projects/utils/udemy-script/output/【한글자막】 Redis 개발자를 위한 Redis 완벽 가이드"

    # Section 19
    print("Processing Section 19...")
    content19 = read_large_file(f"{base_path}/Section_19_섹션 19 RediSearch로 데이터 쿼리하기_total.md")
    if content19:
        material19 = create_section_19_material(content19)
        with open("/Users/jang/projects/utils/udemy-script/Udemy_19_RediSearch.md", 'w', encoding='utf-8') as f:
            f.write(material19)
        print("✓ Section 19 completed: Udemy_19_RediSearch.md")

    # Section 20
    print("Processing Section 20...")
    content20 = read_large_file(f"{base_path}/Section_20_섹션 20 검색 구현하기_total.md")
    if content20:
        material20 = create_section_20_material(content20)
        with open("/Users/jang/projects/utils/udemy-script/Udemy_20_검색_구현.md", 'w', encoding='utf-8') as f:
            f.write(material20)
        print("✓ Section 20 completed: Udemy_20_검색_구현.md")

    # Section 21
    print("Processing Section 21...")
    content21 = read_large_file(f"{base_path}/Section_21_섹션 21 스트림을 통한 서비스 통신_total.md")
    if content21:
        material21 = create_section_21_material(content21)
        with open("/Users/jang/projects/utils/udemy-script/Udemy_21_Streams.md", 'w', encoding='utf-8') as f:
            f.write(material21)
        print("✓ Section 21 completed: Udemy_21_Streams.md")

    print("\n" + "="*50)
    print("All sections completed!")
    print("="*50)

if __name__ == "__main__":
    main()