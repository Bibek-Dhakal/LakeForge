# Changelog

## [0.2.0](https://github.com/Bibek-Dhakal/LakeForge/compare/lakeforge-v0.1.0...lakeforge-v0.2.0) (2026-10-05)


### Features

* **airflow:** provide parallel production-grade PostgreSQL orchestration profile ([1e745c0](https://github.com/Bibek-Dhakal/LakeForge/commit/1e745c0e5af2ee3f3d0f511bafcb83d00000102a))
* **core:** scaffold LakeForge medallion lakehouse with idempotent pipelines, quarantine, governed serving and docs ([46d42d3](https://github.com/Bibek-Dhakal/LakeForge/commit/46d42d39028edeba7eb015eeab4069969845d618))


### Bug Fixes

* **airflow:** run airflow containers as root to resolve volume permission conflicts with pipeline container ([155df9c](https://github.com/Bibek-Dhakal/LakeForge/commit/155df9c92374239154f42e2f69d1600addb18ca5))
* **spark:** resolve native hadoop and truncated string warnings and update usage docs ([0d6defe](https://github.com/Bibek-Dhakal/LakeForge/commit/0d6defe7ff24c8e3c869bf66acf8ba90f9067341))


### Documentation

* add v0.1.0 release notes link to root README ([920a489](https://github.com/Bibek-Dhakal/LakeForge/commit/920a489d6eae7f492224ae52c538c5c5ee8f66e5))
* **observability:** detail target checking and grafana query steps ([d66d136](https://github.com/Bibek-Dhakal/LakeForge/commit/d66d1369dc47e4d490e1e39744a1433e5e54103a))
* **observability:** update deployment guide with UI endpoints and grafana setup ([b9f0bee](https://github.com/Bibek-Dhakal/LakeForge/commit/b9f0beeb09b6280d2e1af1bed5694da96cf96502))
* **release:** generate v0.1.0 pre-release documentation with visual assets ([d1e5f90](https://github.com/Bibek-Dhakal/LakeForge/commit/d1e5f90be8acae3d43d80b0993e1090d3c6659ce))

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
