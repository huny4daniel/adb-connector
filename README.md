# ADB 무선 디버깅 연결 / ADB Wireless Debugging Connector

ADB 무선 디버깅을 GUI 환경에서 간편하게 연결할 수 있는 도구입니다.  
A GUI tool for easily connecting ADB wireless debugging.

## 기능 / Features

- IP/포트 입력으로 ADB 무선 연결 및 해제 / Connect and disconnect ADB wirelessly by entering IP and port
- Android 11+ 페어링 코드 입력 지원 / Pairing code support for Android 11+
- ADB 경로 자동 탐색 및 수동 지정 (설정 저장) / Auto-detect or manually set ADB path (saved to config)
- 연결된 기기 목록 실시간 확인 / View connected devices in real time
- 엔터 키로 빠른 연결 / Quick connect with Enter key
- 로그 영역 성공/실패 색상 구분 / Color-coded log output for success/failure

## 다운로드 / Download

[최신 릴리즈 / Latest Release](https://github.com/huny4daniel/adb-connector/releases/latest)에서 `adb-connector.exe`를 받아 실행하세요.  
Download `adb-connector.exe` from the latest release and run it.

## 사용 방법 / Usage

### Android 10 이하 / Android 10 and below

1. USB로 기기 연결 후 터미널에서 `adb tcpip 5555` 실행  
   Connect via USB and run `adb tcpip 5555` in terminal
2. USB 분리 / Disconnect USB
3. 프로그램에서 기기 IP와 포트(`5555`) 입력 후 연결  
   Enter device IP and port `5555` in the app and connect

### Android 11 이상 (무선 페어링) / Android 11+ (Wireless Pairing)

1. 기기 설정 → 개발자 옵션 → 무선 디버깅 활성화  
   Settings → Developer options → Enable Wireless debugging
2. "페어링 코드로 기기 페어링" 탭 / Tap "Pair device with pairing code"
3. 프로그램 페어링 섹션에 IP, 포트, 코드 입력 후 페어링  
   Enter IP, port, and pairing code in the Pairing section
4. 이후 연결 섹션에서 IP와 디버깅 포트로 연결  
   Then connect using the IP and debugging port in the Connect section

## ADB 경로 설정 / ADB Path Configuration

ADB가 PATH에 등록되지 않은 경우 프로그램 상단에서 직접 지정할 수 있습니다.  
If ADB is not in your PATH, you can set the path manually at the top of the app.

- **자동 탐색 / Auto-detect**: 일반적인 Android SDK 설치 경로 자동 검색 / Searches common Android SDK installation paths
- **찾아보기 / Browse**: `adb.exe` 직접 선택 / Select `adb.exe` manually

설정은 `config.json`에 저장되어 다음 실행 시 자동 로드됩니다.  
Settings are saved to `config.json` and loaded automatically on next launch.

## 직접 실행 / Run from Source

```bash
python adb_connector.py
```
