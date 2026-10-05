# Changelog

## [0.2.0](https://github.com/Bibek-Dhakal/LakeForge/compare/lakeforge-v0.1.0...lakeforge-v0.2.0) (2026-10-05)


### Features

* **airflow:** provide parallel production-grade PostgreSQL orchestration profile ([99bbd9b](https://github.com/Bibek-Dhakal/LakeForge/commit/99bbd9b8d6d2cf15f785f228aebd8508ac18ffc1))
* **core:** scaffold LakeForge medallion lakehouse with idempotent pipelines, quarantine, governed serving and docs ([8a6811b](https://github.com/Bibek-Dhakal/LakeForge/commit/8a6811ba3ff419c7694ff15a4eb72ef45afa799a))


### Bug Fixes

* **airflow:** run airflow containers as root to resolve volume permission conflicts with pipeline container ([b6dac81](https://github.com/Bibek-Dhakal/LakeForge/commit/b6dac81340982dba276ea8cc9b661c0409790585))
* **spark:** resolve native hadoop and truncated string warnings and update usage docs ([54507e9](https://github.com/Bibek-Dhakal/LakeForge/commit/54507e9a13edb857b3a332425e4897e4d4487cce))


### Documentation

* add v0.1.0 release notes link to root README ([42e07fc](https://github.com/Bibek-Dhakal/LakeForge/commit/42e07fcaaa5c23baa69c1346c66616c270a6ed71))
* **observability:** detail target checking and grafana query steps ([a60acd7](https://github.com/Bibek-Dhakal/LakeForge/commit/a60acd7e3215c15aa3008133252989681a47300d))
* **observability:** update deployment guide with UI endpoints and grafana setup ([f6630c6](https://github.com/Bibek-Dhakal/LakeForge/commit/f6630c6f10f858be7cfb4332204492d0da098073))
* **release:** generate v0.1.0 pre-release documentation with visual assets ([c6ba0a8](https://github.com/Bibek-Dhakal/LakeForge/commit/c6ba0a86758d9c090a152955184dbc07bc5d6105))

## 0.1.0 (2026-10-05)


### Features

* **airflow:** provide parallel production-grade PostgreSQL orchestration profile ([76d4005](https://github.com/Bibek-Dhakal/LakeForge/commit/76d4005b88cd61a346bd0c7569287f91564117b5))
* **core:** scaffold LakeForge medallion lakehouse with idempotent pipelines, quarantine, governed serving and docs ([791612e](https://github.com/Bibek-Dhakal/LakeForge/commit/791612ef3414f835a11f4ff0621ac2b14b5fb7c8))


### Bug Fixes

* **airflow:** run airflow containers as root to resolve volume permission conflicts with pipeline container ([0382469](https://github.com/Bibek-Dhakal/LakeForge/commit/0382469cd61467f6bb2cdc1ba2da41e49a4f1cee))
* **spark:** resolve native hadoop and truncated string warnings and update usage docs ([6fea42c](https://github.com/Bibek-Dhakal/LakeForge/commit/6fea42c700310fde75550fb263f545a10a8a8c72))


### Documentation

* **observability:** detail target checking and grafana query steps ([6915d02](https://github.com/Bibek-Dhakal/LakeForge/commit/6915d02bf9529c024a2605fbeb173bea72786a5d))
* **observability:** update deployment guide with UI endpoints and grafana setup ([f876a0c](https://github.com/Bibek-Dhakal/LakeForge/commit/f876a0cb2e956c321564119c23bbf3b5b19557e2))
* **release:** generate v0.1.0 pre-release documentation with visual assets ([d849a8a](https://github.com/Bibek-Dhakal/LakeForge/commit/d849a8abcb7bbb0402a93408382ce8bd9a0b81ae))
