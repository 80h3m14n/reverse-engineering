/**********************************************************************
 * odfhex - Modernized objdump / hexdump to C/C++ shellcode extractor
 * 
 * Original by Steve Hanna (vividmachines.com) v0.1
 * - https://www.vividmachines.com/shellcode/odfhex.cpp
 *
 * Cleaned, fixed, and improved version - 2026
 * Features:
 *   - Robust parsing of common objdump -d, xxd, hexdump -C, od outputs
 *   - Automatic detection of byte patterns (no more "skip 4 colons")
 *   - Optional XOR obfuscation (-x <value>)
 *   - Output as escaped C string literal (default) or byte array
 *   - Proper error handling, RAII, modern C++17
 *   - Support for stdin / files
 *   - Line wrapping, clean formatting
 *   - Reads from file or stdin ("-")
 *
 * Usage:
 *   odfhex <dumpfile> | -> [-x <hex>] [--array] [-h |--help]
 * or
 *   objdump -d your_binary | ./odfhex -
 * or
 *   ./odfhex dump.txt -x aa # with XOR
 *
 * Compile:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic odfhex.cpp -o odfhex
 **********************************************************************/

#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <iomanip>
#include <sstream>
#include <cctype>
#include <charconv>
#include <optional>
#include <cstdint>      // Required for uint8_t
#include <cstring>      // for std::strlen

namespace {

    constexpr size_t BYTES_PER_LINE = 16;  // Clean, standard line length

    // Trim whitespace from string_view
    std::string_view trim(std::string_view s) {
        size_t start = s.find_first_not_of(" \t\r\n");
        if (start == std::string_view::npos) return {};
        size_t end = s.find_last_not_of(" \t\r\n");
        return s.substr(start, end - start + 1);
    }

    // Safely parse two-digit hex byte
    std::optional<uint8_t> parse_hex_byte(std::string_view hex) {
        if (hex.size() != 2) return std::nullopt;

        uint8_t value = 0;
        auto [ptr, ec] = std::from_chars(hex.data(), hex.data() + 2, value, 16);
        if (ec != std::errc{} || ptr != hex.data() + 2) {
            return std::nullopt;
        }
        return value;
    }

    // Extract hex bytes from a single line (robust across common dump formats)
    std::vector<uint8_t> extract_bytes_from_line(std::string_view line) {
        std::vector<uint8_t> bytes;
        line = trim(line);
        if (line.empty()) return bytes;

        for (size_t i = 0; i + 1 < line.size(); ++i) {
            if (std::isxdigit(static_cast<unsigned char>(line[i])) &&
                std::isxdigit(static_cast<unsigned char>(line[i + 1]))) {

                // Heuristic: byte likely if preceded by whitespace, :, | or at start
                // and followed by whitespace, :, | or end
                bool is_byte = (i == 0) ||
                std::isspace(static_cast<unsigned char>(line[i - 1])) ||
                line[i - 1] == ':' || line[i - 1] == '|';

            if (is_byte) {
                if (i + 2 == line.size() ||
                    std::isspace(static_cast<unsigned char>(line[i + 2])) ||
                    line[i + 2] == '|' || line[i + 2] == ':') {

                    if (auto b = parse_hex_byte(line.substr(i, 2))) {
                        bytes.push_back(*b);
                        ++i;  // Skip the second hex digit
                    }
                    }
            }
                }
        }
        return bytes;
    }

} // anonymous namespace

int main(int argc, char** argv) {
    std::cout << "odfhex - objdump/hexdump → C/C++ shellcode extractor (modernized)\n\n";

    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <dumpfile | - for stdin> [-x <xor_hex>] [--array]\n";
        std::cerr << "       --array   Output as uint8_t array{...} instead of string\n";
        std::cerr << "       -h|--help Show this help\n\n";
        return 1;
    }

    std::string input_path = argv[1];
    std::optional<uint8_t> xor_key = std::nullopt;
    bool output_as_array = false;

    for (int i = 2; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "-x" || arg == "--xor") {
            if (i + 1 >= argc) {
                std::cerr << "Error: -x requires a hex value (e.g. AA)\n";
                return 1;
            }
            uint8_t key = 0;
            auto [ptr, ec] = std::from_chars(argv[i + 1], argv[i + 1] + std::strlen(argv[i + 1]), key, 16);
            if (ec != std::errc{} || ptr == argv[i + 1]) {
                std::cerr << "Error: Invalid XOR value (must be 00-FF in hex)\n";
                return 1;
            }
            xor_key = key;
            ++i;
        }
        else if (arg == "--array") {
            output_as_array = true;
        }
        else if (arg == "-h" || arg == "--help") {
            std::cout << "Supported input formats: objdump -d, xxd -g1, hexdump -C, od -tx1, etc.\n";
            return 0;
        }
    }

    // Open input (file or stdin)
    std::ifstream file;
    std::istream* input_stream = &std::cin;

    if (input_path != "-") {
        file.open(input_path, std::ios::in);
        if (!file.is_open()) {
            std::cerr << "Error: Could not open file '" << input_path << "'\n";
            return 1;
        }
        input_stream = &file;
    }

    std::vector<uint8_t> shellcode;
    std::string line;
    while (std::getline(*input_stream, line)) {
        auto bytes = extract_bytes_from_line(line);
        shellcode.insert(shellcode.end(), bytes.begin(), bytes.end());
    }

    if (shellcode.empty()) {
        std::cerr << "Error: No valid hex bytes found in input.\n";
        std::cerr << "       Try objdump -d binary | ./odfhex -\n";
        return 1;
    }

    // Apply XOR if requested
    if (xor_key.has_value()) {
        std::cout << "Applying XOR key 0x"
        << std::hex << std::setw(2) << std::setfill('0')
        << static_cast<int>(*xor_key) << std::dec << "\n";
        for (auto& b : shellcode) {
            b ^= *xor_key;
        }
    }

    std::cout << "Successfully extracted " << shellcode.size() << " bytes.\n\n";

    // === Output section ===
    if (output_as_array) {
        std::cout << "unsigned char shellcode[] = {\n";
        for (size_t i = 0; i < shellcode.size(); ++i) {
            if (i % BYTES_PER_LINE == 0) {
                std::cout << "    ";
            }
            std::cout << "0x" << std::hex << std::setw(2) << std::setfill('0')
            << static_cast<int>(shellcode[i]) << std::dec;
            if (i + 1 < shellcode.size()) {
                std::cout << ",";
            }
            if ((i + 1) % BYTES_PER_LINE == 0 || i + 1 == shellcode.size()) {
                std::cout << "\n";
            } else {
                std::cout << " ";
            }
        }
        std::cout << "};\n";
    } else {
        // Classic escaped string literal
        std::cout << "char shellcode[] =\n\"";
        for (size_t i = 0; i < shellcode.size(); ++i) {
            std::cout << "\\x" << std::hex << std::setw(2) << std::setfill('0')
            << static_cast<int>(shellcode[i]) << std::dec;

            if ((i + 1) % BYTES_PER_LINE == 0 && i + 1 < shellcode.size()) {
                std::cout << "\"\\\n\"";
            }
        }
        std::cout << "\";\n";
    }

    std::cout << "\n// " << shellcode.size() << " bytes ready for use.\n";
    return 0;
}
