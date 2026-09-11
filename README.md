## Reverse Engineering (RE)

A structured map of reverse engineering concepts, techniques, tools, resources, and practical labs.

### What is Reverse Engineering?

Reverse engineering is the process of analyzing a system,program, binary, protocol, or device to understand how it works, often without access to its original source or design.


### Subfields of RE

Reverse engineering breaks down into a few overlapping subfields, usually organized by what is being reversed and what tools you're using. 

| Field                     | Description                                |
|---------------------------|--------------------------------------------|
| Static Analysis           | Analyze software without executing it      |
| Dynamic Analysis          | Analyze software during execution          |
| Binary Analysis           | Analyze compiled machine-code programs     |
| Malware Analysis          | Understand malicious software              |
| Vulnerability Research    | Find & understand software vulnerabilities |
| Firmware RE               | Analyze embedded-device firmware           |
| Mobile RE                 | Analyze Android/iOS applications           |
| Network protocol Analysis | Reverse engineer communication protocols   |
| Program Analysis          | Analyze program structure and behavior     |


The above table only focuses on fields related to cyber security


### Learning Path

1. Computer architecture
2. C/C/C++ fundamentals
3. Assembly
4. Operating systems
5. Executable formats
6. Static analysis
7. Debugging and dynamic analysis
8. Binary analysis
9. Malware analysis
10. Vulnerability research



### Navigating the repo (not fully implemented)


<details>
<summary>📂 Click to expand</summary>

```ini
reverse-engineering/
├── 01-foundations/
│   ├── computer-architecture/
│   ├── operating-systems/
│   ├── programming-languages/
│   ├── assembly/
│   ├── memory-and-processes/
│   └── executable-formats/
│
├── 02-static-analysis/
│   ├── disassembly/
│   ├── decompilation/
│   ├── control-flow-analysis/
│   ├── data-flow-analysis/
│   ├── string-analysis/
│   └── binary-signatures/
│
├── 03-dynamic-analysis/
│   ├── debugging/
│   ├── tracing/
│   ├── instrumentation/
│   ├── system-calls/
│   ├── memory-analysis/
│   └── runtime-behavior/
│
├── 04-binary-analysis/
│   ├── x86/
│   ├── x86-64/
│   ├── arm/
│   ├── arm64/
│   ├── elf/
│   ├── pe/
│   ├── macho/
│   └── binary-parsing/
│
├── 05-malware-analysis/
│   ├── static-malware-analysis/
│   ├── dynamic-malware-analysis/
│   ├── unpacking/
│   ├── obfuscation/
│   ├── persistence/
│   └── behavioral-analysis/
│
├── 06-vulnerability-research/
│   ├── memory-corruption/
│   ├── fuzzing/
│   ├── crash-analysis/
│   ├── patch-diffing/
│   └── exploit-mitigation-analysis/
│
├── 07-firmware-and-embedded/
│   ├── firmware-extraction/
│   ├── embedded-architectures/
│   ├── hardware-interfaces/
│   ├── boot-process/
│   └── firmware-analysis/
│
├── 08-mobile-reversing/
│   ├── android/
│   ├── ios/
│   ├── apk-analysis/
│   └── mobile-native-code/
│
├── 09-network-and-protocol-analysis/
│   ├── protocol-reconstruction/
│   ├── packet-analysis/
│   ├── custom-protocols/
│   └── client-server-analysis/
│
├── 10-program-analysis/
│   ├── control-flow-graphs/
│   ├── call-graphs/
│   ├── symbolic-execution/
│   ├── taint-analysis/
│   └── intermediate-representations/
│
└── 11-resources/
    ├── books.md
    ├── courses.md
    ├── papers.md
    ├── tools.md
    └── websites.md
```

</details>


### RE tips

- [x] Understand before you modify
- [x] Always work in an isolated enviroment i.e virtual machine
- [x] Document everything
- [x] Verify assumptions with evidence 
- [x] Reverse engineering is about curious minds, smart tools and systematic analysis
- [x] Always respect laws, licenses and ethical boundaries
- [x] Reverse engineering is a blackbox procedure 



>Deconstruct. Reconstruct. Understand.

