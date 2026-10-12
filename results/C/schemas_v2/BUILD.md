# router schema v2 build (dev half of ko_massive_domain_8, 250 rows; source: data/evals/ko_massive_domain_8.jsonl sha256 edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b)

| variant | file | rows | options | dataset sha256 | questions_sha256 | note |
|---|---|---|---|---|---|---|
| v1 | results/C/schemas_v2/router_v1_dev.jsonl | 250 | 8 | a8223a39cd879c94a60eb0bd9c30fa56813065d255a3ddd54593debab3102536 | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | baseline router_v1 (questions byte-identical to data/evals/ko_massive_domain_8.jsonl) |
| v2a | results/C/schemas_v2/router_v2a_dev.jsonl | 250 | 8 | bc18386eecd77d08d99c246d67d7c09d1fd9fcac2225ac55da487a6b18298b81 | c8b97badf47449eb3891c31f0d55e9633406ff5d34673b6edbe69024c9b65702 | sharpened descriptions, same 8 keys, same order |
| v2b | results/C/schemas_v2/router_v2b_dev.jsonl | 220 | 7 | 9a553debb9f158b260276a916b89a729b78a022018191f6367d22ed92b7a5bf5 | c38ebc7c16da21e6ed6faa6c1e826ce52bc1e99ea8876c23431325315422a4bd | v2a without general (7 options) |
| v2b_general | results/C/schemas_v2/router_v2b_dev_general.jsonl | 30 | 7 | 557c0037262aab0567ddbc7304580f4f5d200a98dde7876d8048fafc5675c6e4 | c38ebc7c16da21e6ed6faa6c1e826ce52bc1e99ea8876c23431325315422a4bd | v2a without general (7 options) | gold general is outside this schema: unscorable rows, for the confidence-gate analysis only |
| v2c | results/C/schemas_v2/router_v2c_dev.jsonl | 250 | 8 | 4c1a473e414e59cb683d8c36f5289147c4932f1658b788ec71b5ff72b95f38b4 | c26e216fda3fd2057ae3ed4baaf68a885267d65ad57a21a00e98a3dccf95a073 | v2a + 2 example utterances per description |
| v2d | results/C/schemas_v2/router_v2d_dev.jsonl | 250 | 8 | da73a646a05a92a211f823c73dfb936a774ce8cdbbc7356527685507c43a0147 | 5bdac5b744e7fc4bffdb32e9856f8f52f116f8a51a8bdb4c62c8500ea94283e6 | v2a reordered: general first, smart_home last |
| v2e | results/C/schemas_v2/router_v2e_dev.jsonl | 220 | 5 | 8cabdc1523e3d25b95191de7478e6280df44491e82bef41ba3c4761e68502a4d | 4eeb2f06eb82ccc71fc85556d74857e5b79473586e73f50f3050f4c36d957866 | 5-class coarse taxonomy (assistant_tasks, media, smart_home, info_qa, daily_life) |
| v2e_general | results/C/schemas_v2/router_v2e_dev_general.jsonl | 30 | 5 | 0c7a109f14a7cbda6cc8ba9beff85a4d3b28b57ee215e86848c4a085ee2d5d4a | 4eeb2f06eb82ccc71fc85556d74857e5b79473586e73f50f3050f4c36d957866 | 5-class coarse taxonomy (assistant_tasks, media, smart_home, info_qa, daily_life) | gold general is outside this schema: unscorable rows, for the confidence-gate analysis only |

v2c examples vs states (normalized: whitespace and .,!?~'" removed): 16 examples, exact matches with dev states none, exact matches anywhere in the 500-row file 0, dev substring containments none

## head budget (multilingual, tokenizer only)

Per option: 1 [MASK] + tokens of ' key: description', each capped at 48 by the tokenizer (laya/common.py build_head). If the options exceed head_max_len - 16, every option is cut to max(4, (head_max_len - 16) // k) tokens.

| variant | head_max_len | tokens per option (uncapped) | sum | per-option cap applied | head length | options as the model sees them |
|---|---|---|---|---|---|---|
| v1 | 256 | [21, 24, 29, 25, 18, 24, 16, 24] | 181 | None | 199 | productivity: 알람, 일정, 날짜와 시간, 할 일과 쇼핑 목록 / media: 음악, 라디오, 팟캐스트, 오디오북 재생과 음량 조절 / smart_home: 조명, 커피머신, 청소기, 플러그 등 스마트홈 기기 제어 / info_qa: 사실, 정의, 계산, 환율, 날씨, 뉴스 등 정보 질문 / communication: 이메일, 연락처, 소셜 미디어 게시와 확인 / lifestyle: 음식 주문과 배달, 요리법, 장소·이벤트·영화 추천 / transport: 교통, 택시, 티켓, 길 안내 / general: 인사, 잡담, 농담, 위 어디에도 속하지 않는 일반 대화 |
| v2a | 256 | [32, 30, 45, 29, 25, 24, 23, 26] | 234 | None | 252 | productivity: 알람·타이머 설정, 일정 등록·조회, 날짜·시간 질문, 할 일·쇼핑 목록 관리 / media: 음악·라디오·팟캐스트·오디오북 재생과 음량·음소거 같은 오디오 조절 / smart_home: 조명, 커피머신, 청소기, 플러그 등 집안 기기를 켜고 끄거나 설정 변경 (오디오 재생·음량은 제외) / info_qa: 날씨, 뉴스, 사실·정의·계산·환율 같은 정보를 묻는 질문 / communication: 이메일 보내기·확인, 연락처, 소셜 미디어 게시·확인 / lifestyle: 음식 주문·배달, 요리법, 장소·이벤트·영화 추천 / transport: 교통, 택시 호출, 기차·항공 티켓, 길 안내 / general: 인사, 농담, 안부, 잡담처럼 특정 작업을 요청하지 않는 대화 |
| v2b | 256 | [32, 30, 45, 29, 25, 24, 23] | 208 | None | 226 | productivity: 알람·타이머 설정, 일정 등록·조회, 날짜·시간 질문, 할 일·쇼핑 목록 관리 / media: 음악·라디오·팟캐스트·오디오북 재생과 음량·음소거 같은 오디오 조절 / smart_home: 조명, 커피머신, 청소기, 플러그 등 집안 기기를 켜고 끄거나 설정 변경 (오디오 재생·음량은 제외) / info_qa: 날씨, 뉴스, 사실·정의·계산·환율 같은 정보를 묻는 질문 / communication: 이메일 보내기·확인, 연락처, 소셜 미디어 게시·확인 / lifestyle: 음식 주문·배달, 요리법, 장소·이벤트·영화 추천 / transport: 교통, 택시 호출, 기차·항공 티켓, 길 안내 |
| v2c | 256 | [58, 51, 65, 50, 50, 48, 49, 47] | 418 | 30 | 258 | productivity: 알람·타이머 설정, 일정 등록·조회, 날짜·시간 질문, 할 일·쇼핑 / media: 음악·라디오·팟캐스트·오디오북 재생과 음량·음소거 같은 오디오 조절 / smart_home: 조명, 커피머신, 청소기, 플러그 등 집안 기기를 켜고 끄 / info_qa: 날씨, 뉴스, 사실·정의·계산·환율 같은 정보를 묻는 질문 예 / communication: 이메일 보내기·확인, 연락처, 소셜 미디어 게시·확인 예: '김 과 / lifestyle: 음식 주문·배달, 요리법, 장소·이벤트·영화 추천 예: '치킨 배 / transport: 교통, 택시 호출, 기차·항공 티켓, 길 안내 예: '강남역까지 / general: 인사, 농담, 안부, 잡담처럼 특정 작업을 요청하지 않는 대화 예: '안 |
| v2c | 512 | [58, 51, 65, 50, 50, 48, 49, 47] | 418 | None | 407 | productivity: 알람·타이머 설정, 일정 등록·조회, 날짜·시간 질문, 할 일·쇼핑 목록 관리 예: '내일 아침 7시에 깨워줘', ' / media: 음악·라디오·팟캐스트·오디오북 재생과 음량·음소거 같은 오디오 조절 예: '아이유 노래 틀어줘', '소리 좀 줄여 / smart_home: 조명, 커피머신, 청소기, 플러그 등 집안 기기를 켜고 끄거나 설정 변경 (오디오 재생·음량은 제외) 예: '거 / info_qa: 날씨, 뉴스, 사실·정의·계산·환율 같은 정보를 묻는 질문 예: '이번 주말 날씨 어때', '달러 환율 얼마야 / communication: 이메일 보내기·확인, 연락처, 소셜 미디어 게시·확인 예: '김 과장한테 메일 보내줘', '페이스북 새 소식 보여줘 / lifestyle: 음식 주문·배달, 요리법, 장소·이벤트·영화 추천 예: '치킨 배달 시켜줘', '김치찌개 끓이는 법 알려줘' / transport: 교통, 택시 호출, 기차·항공 티켓, 길 안내 예: '강남역까지 택시 불러줘', '부산 가는 KTX 예매해줘' / general: 인사, 농담, 안부, 잡담처럼 특정 작업을 요청하지 않는 대화 예: '안녕 잘 지냈어', '재미있는 농담 하나 해줘' |
| v2d | 256 | [26, 32, 30, 29, 25, 24, 23, 45] | 234 | None | 252 | general: 인사, 농담, 안부, 잡담처럼 특정 작업을 요청하지 않는 대화 / productivity: 알람·타이머 설정, 일정 등록·조회, 날짜·시간 질문, 할 일·쇼핑 목록 관리 / media: 음악·라디오·팟캐스트·오디오북 재생과 음량·음소거 같은 오디오 조절 / info_qa: 날씨, 뉴스, 사실·정의·계산·환율 같은 정보를 묻는 질문 / communication: 이메일 보내기·확인, 연락처, 소셜 미디어 게시·확인 / lifestyle: 음식 주문·배달, 요리법, 장소·이벤트·영화 추천 / transport: 교통, 택시 호출, 기차·항공 티켓, 길 안내 / smart_home: 조명, 커피머신, 청소기, 플러그 등 집안 기기를 켜고 끄거나 설정 변경 (오디오 재생·음량은 제외) |
| v2e | 256 | [26, 30, 45, 29, 19] | 149 | None | 167 | assistant_tasks: 알람·일정·시간·목록·이메일·소셜 등 비서 작업 / media: 음악·라디오·팟캐스트·오디오북 재생과 음량·음소거 같은 오디오 조절 / smart_home: 조명, 커피머신, 청소기, 플러그 등 집안 기기를 켜고 끄거나 설정 변경 (오디오 재생·음량은 제외) / info_qa: 날씨, 뉴스, 사실·정의·계산·환율 같은 정보를 묻는 질문 / daily_life: 음식·요리·추천·교통·이동 |

## words shared across options (regex [가-힣A-Za-z0-9]+, no stemming: josa-attached forms count as different words)

- v1: smart_home ∩ info_qa: 등
- v2a: productivity ∩ smart_home: 설정; productivity ∩ info_qa: 질문; media ∩ smart_home: 오디오; media ∩ info_qa: 같은
- v2b: productivity ∩ smart_home: 설정; productivity ∩ info_qa: 질문; media ∩ smart_home: 오디오; media ∩ info_qa: 같은
- v2c: productivity ∩ smart_home: 설정; productivity ∩ info_qa: 질문; media ∩ smart_home: 오디오; media ∩ info_qa: 같은
- v2d: productivity ∩ info_qa: 질문; productivity ∩ smart_home: 설정; media ∩ info_qa: 같은; media ∩ smart_home: 오디오
- v2e: assistant_tasks ∩ smart_home: 등; media ∩ smart_home: 오디오; media ∩ info_qa: 같은
