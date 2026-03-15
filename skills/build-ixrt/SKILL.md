---
name: build-ixrt
description: 在天数容器中编译 ixrt 源码，生成 C++ 库和 Python wheel 包。当用户说"编译 ixrt"、"build ixrt"、"打包 ixrt"时使用。
argument-hint: [源码路径，默认 /tmp/ixrt]
---

在容器 `yzc_ixrt_compiler` 中编译 ixrt 源码，生成 C++ 库（`.so`）和 Python wheel 包。

源码路径默认为 `/tmp/ixrt`，也可通过 `$ARGUMENTS` 指定其他路径。

## 执行步骤

按以下顺序逐步执行，每步完成后再进行下一步：

### 1. 确定源码路径
```
IXRT_SRC=${ARGUMENTS:-/tmp/ixrt}
```

### 2. 安装系统依赖
```bash
docker exec yzc_ixrt_compiler bash -c "apt update -qq && apt install -y libgmp-dev libxml2-dev wget rsync && pip install wheel -q"
```

### 3. 准备 IXCC（若不存在则下载）

检查 `/opt/tests/ixcc/ixcc/llvm/build/lib` 是否存在：
```bash
docker exec yzc_ixrt_compiler bash -c "ls /opt/tests/ixcc/ixcc/llvm/build/lib >/dev/null 2>&1 && echo EXISTS || echo MISSING"
```

若 MISSING，执行：
```bash
docker exec yzc_ixrt_compiler bash -c "
  mkdir -p /opt/tests/ixcc && cd /opt/tests/ixcc
  wget -q --show-progress http://10.150.9.95/swapp/software/ixcc-18_x86_ubuntu.tar.gz
  tar zxf ixcc-18_x86_ubuntu.tar.gz && rm ixcc-18_x86_ubuntu.tar.gz
  # 修复 cmake 硬编码路径
  [ -L /opt/tests/ixcc/llvm ] || ln -s /opt/tests/ixcc/ixcc/llvm /opt/tests/ixcc/llvm
"
```

注意：下载文件约 1.5G，需要等待较长时间。

### 4. CMake 配置
```bash
docker exec yzc_ixrt_compiler bash -c "
  cd ${IXRT_SRC}
  export llvm_lib_dir=/opt/tests/ixcc/ixcc/llvm/build/lib
  cmake -B build -DIXRT_LLVM_LIB_DIR=\${llvm_lib_dir}
"
```

### 5. 编译 C++ 库（耗时较长，在后台运行）
```bash
docker exec yzc_ixrt_compiler bash -c "cd ${IXRT_SRC} && cmake --build build -j"
```

编译完成后验证产物：
```bash
docker exec yzc_ixrt_compiler bash -c "find ${IXRT_SRC}/build/lib -name '*.so' | sort"
```

期望看到：`libixrt.so`、`libixrt_lean.so`、`libixrt_builder_resource.so`、`libixrtonnxparser.so`、`libixrt_plugin.so`

### 6. 构建 Python wheel
```bash
docker exec yzc_ixrt_compiler bash -c "cd ${IXRT_SRC} && IXRT_ARCH=NEW bash tools/dist/build_ixrt.sh"
```

完成后验证：
```bash
docker exec yzc_ixrt_compiler bash -c "find ${IXRT_SRC}/build_pip -name '*.whl'"
```

## 注意事项

- 步骤 3（下载 ixcc）和步骤 5（cmake --build）耗时最长，需耐心等待
- 若 cmake 已配置过（`build/` 目录存在），可跳过步骤 4
- 若 C++ 库已编译（`build/lib/libixrt.so` 存在），可直接跳到步骤 6
- `prepare_build_deps.sh` 脚本使用 sudo，容器内 root 环境需手动替代执行
- LLVM cmake 配置文件硬编码了 `/opt/tests/ixcc/llvm` 路径，必须确保软链接存在

## 安装 wheel

```bash
docker exec yzc_ixrt_compiler pip install ${IXRT_SRC}/build_pip/ixrt-*.whl
```
