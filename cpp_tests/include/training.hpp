#pragma once
#include <cmath>
#include <cstddef>
#include <string>

struct DataProcessor {
  static float processFloat(float f) {
    if (std::isnan(f) || std::isinf(f)) {
      return 0.0f;
    }
    return f;
  }
};

struct ConfigManager {
  static bool validateConfig(const std::string &config) {
    return !config.empty();
  }
};

struct Utility {
  static int safeAccessArray(int *arr, std::size_t size, std::size_t index) {
    if (arr == nullptr || index >= size) {
      return -1;
    }
    return arr[index];
  }
};
