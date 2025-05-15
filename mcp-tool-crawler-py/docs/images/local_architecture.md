# Local Architecture Diagram

```mermaid
flowchart TD
    CLI[Command Line Interface] --> SM & CL & CP
    SM[Source Management] --> DB[(SQLite Database)]
    CL[Crawler Logic] --> OAI[OpenAI API]
    CP[Catalog Processing] --> FS[(Local File Storage)]
    
    subgraph Storage
        DB
        FS
    end
    
    subgraph Core Logic
        SM
        CL
        CP
    end
    
    subgraph User Interface
        CLI
    end
    
    subgraph External Services
        OAI
        GH[GitHub API]
    end
    
    CL --> GH
```

# Workflow Diagram

```mermaid
flowchart TD
    IS[Initialize Sources] --> GS[Get Sources To Crawl]
    GS --> MS[Map Sources To Process]
    MS --> CS[Check Crawler Strategy]
    CS --> KC[Known Crawler] & GC[Generate Crawler] & EC[Execute Crawler]
    KC --> EC
    GC --> EC
    EC --> RR[Record Result]
    
    subgraph Finalization
        PC[Process Catalog] --> N[Notification]
    end
    
    RR --> PC
    note[After all sources processed] -.- PC
```

# Migration Flow

```mermaid
flowchart LR
    AWS[(AWS Services)] --> EX[Export Scripts]
    EX --> MF[Migration Files]
    MF --> IM[Import Scripts]
    IM --> SQ[(SQLite Database)]
    IM --> FS[(Local File Storage)]
    
    subgraph AWS Storage
        DDB[(DynamoDB)]
        S3[(S3 Bucket)]
    end
    
    subgraph Local Storage
        SQ
        FS
    end
    
    AWS --> AWS Storage
    AWS Storage --> EX
    
    style AWS fill:#FF9900,stroke:#232F3E,stroke-width:2px
    style SQ fill:#003B57,stroke:#003B57,stroke-width:2px
    style FS fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
```

