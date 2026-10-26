# Work B — 최초 판단의 실제 시장 경로 검증

최초 원문·v84의51/60점은 그대로 보존했다. 이번에는 동일10건의20·60·120시장거래일 실제 가격을 대조했으며, 실제 주문·체결·계좌 모의매매는 만들지 않았다.

**진단:** E09는 좋은 진입 위치를 골랐다는 가격 증거가 가장 뚜렷하다. E02는 깊은 예약 미체결, E04/E05는 초기 상승 뒤 가격 접근, E03/E10은 근거 있는 관망이었다. 매도 계약이 없어 어느 경우도 최고가 수익을 실력으로 인정하지 않았다. E08은 사전 기업사건 입력 누락·거래정지로 일반 타점 평가에서 제외한다.

- [10건 최초 조건과 시장 결과 대조](01_CASE_MARKET_VERIFICATION.md)
- [실력 진단·PD-01의 한계·추가 PD-02 후보](02_DIAGNOSIS_AND_PD02.md)
- [시간순 원시가격 사건 근거](CHRONOLOGICAL_EVIDENCE.json), [사례별 결론](CASE_VERDICTS.json)
- [원래 조건 복원](ORIGINAL_CONDITIONS.json), [중요 가격별 첫 관측](ORIGINAL_ANCHOR_OBSERVATIONS.csv)
- [제공된120일 가격 경로, 실명·코드 제외](PATHS_KRW.csv)
- [최초 원문 보존 복사](ORIGINAL_FIRST_ANSWER_UNCHANGED.md), [v84 원점수 보존 복사](V84_ORIGINAL_SCORES_UNCHANGED.json)
- [검증 기록](PRESERVATION_AND_VALIDATION.json), [사후 진단 지문](MARKET_FINDINGS_FREEZE.json)
- [읽기 전용 검증 코드](check_evidence.py): 원문/점수·30개 창·가격 사건·검열 처리를 재검증한다.

최초 원문SHA256: `f4ab10186560a5742862ce596d1686c3d1fb25f22639329a7c86807f17f2cf5f`
v84 점수 파일SHA256: `0f86f1a5bd43655350d4a82ad7a9c25df5bf11fa7559743ebaea10ed28e11a7f`.

PD-01/PD-02 개선 효과·독립 검토·전이·경제적 우위는 미검증이다. 모든10건은 이미정답/매핑/실제후속경로에노출됐으므로미학습표본으로재사용하지않는다. S02와모든운영금지사항유지.
