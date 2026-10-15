<!-- If you're reading the raw markdown: you're my kind of person. Say hi. -->

<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=24&pause=1200&color=D4A373&center=true&vCenter=true&width=640&lines=Hi%2C+I'm+Gonzalo+%F0%9F%91%8B;Full+Stack+Developer;Hexagonal+backends+%C2%B7+Feature-Sliced+frontends;From+bare-metal+Proxmox+to+React+PWAs;SOLID+by+design%2C+not+by+slogan" alt="Hi, I'm Gonzalo. Full Stack Developer." />

<a href="https://mi-portafolio-gonzalo.vercel.app/"><img src="https://img.shields.io/badge/Portfolio-000000?style=for-the-badge&logo=vercel&logoColor=white" alt="Portfolio" /></a>
<a href="https://www.linkedin.com/in/gonzalo-martinez-garcia-353507370"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn" /></a>
<a href="https://gonzaloapps.es/"><img src="https://img.shields.io/badge/Gonzalo_Apps-D4A373?style=for-the-badge&logo=googleplay&logoColor=black" alt="Gonzalo Apps" /></a>
<img src="https://img.shields.io/badge/Open_to_work-2EA043?style=for-the-badge" alt="Open to work" />

</div>

```console
$ whoami
gonzalo — full stack developer · Palma de Mallorca, Spain 🏝️

$ cat about.txt
I build complete applications for the web, desktop and mobile, and the
infrastructure they run on. Systems and networking background, so I like
knowing what happens below the framework too.
```

## 🧭 How I build

```yaml
# ~/.config/gonzalo/principles.yml
architecture: hexagonal        # domain at the core, I/O at the edges
frontend:     feature-sliced   # each slice owns its feature, no spaghetti imports
solid:
  srp: one reason to change, not one verb
  ocp: new case means new code; proven logic stays untouched
  lsp: implementations honor the contract, no surprise errors
  isp: small interfaces, zero "not supported"
  dip: the domain depends on abstractions, never on the database
dry:        about knowledge, not about similar-looking lines
tests:      part of the feature, not an afterthought
dead_code:  0                  # every change removes what it replaces
decisions:  documented         # ADRs, runbooks, diagrams
```

## 🏗️ Featured build

Designed, built and deployed **solo, from an empty server room**: a microservices platform for a field-services company.

```mermaid
flowchart LR
    push(["git push"]) --> ci["Forgejo Actions<br/>test · build · publish"]
    ci --> reg[("Private<br/>registry")]
    reg -->|deploy| pve

    subgraph pve["Proxmox VE"]
        direction LR
        subgraph dmz["DMZ VLAN"]
            proxy["Nginx Proxy Manager"]
        end
        subgraph lan["Internal VLAN"]
            pwa["React PWAs<br/>Feature-Sliced Design"]
            iam["IAM<br/>JWT · RBAC · rate limiting"]
            svc["Spring Boot services<br/>Hexagonal"]
            mq{{"RabbitMQ<br/>Transactional Outbox"}}
            db[("PostgreSQL 17<br/>DB per service")]
        end
    end

    users(["Employees & admins"]) --> proxy --> pwa
    pwa --> iam
    pwa --> svc
    svc --> mq
    svc --> db
    iam --> db
```

**5** microservices · **500+** automated tests · **7** granular RBAC permissions · CI/CD built from scratch

## 🚀 Projects

| Project | What it is | Built with |
|---|---|---|
| [**Quotidia**](https://gonzaloapps.es/apps/quotidia/) | Daily planner for mobile | Flutter · Dart · Kotlin |
| [**License Generator**](https://github.com/gonzapersonalsite/license-generator-docs) | Offline desktop app for RSA-signed software licenses | C# · .NET · Avalonia UI |
| [**NutriManager**](https://github.com/gonzapersonalsite/nutrimanager-docs) | Desktop app for nutritionists: patients, diet plans, PDF reports | .NET 8 · Avalonia UI · SQLite |
| [**Kanban Board**](https://github.com/gonzapersonalsite/kanban-board-app) | Trello-style board running fully in the browser | React · TypeScript · Zustand · FSD |
| [**Pokédex**](https://github.com/gonzapersonalsite/pokedex) | PWA with infinite scroll, filters and evolution chains | React · TanStack Query · Tailwind |

## 🧰 Toolbox

<p>
  <b>Frontend</b><br/>
  <img src="https://skillicons.dev/icons?i=react,ts,js,vite,materialui,tailwind,vue,vitest" alt="React, TypeScript, JavaScript, Vite, Material UI, Tailwind CSS, Vue, Vitest" />
</p>
<p>
  <b>Backend</b><br/>
  <img src="https://skillicons.dev/icons?i=java,spring,hibernate,nodejs,rabbitmq,postgres,mongodb,sqlite" alt="Java, Spring Boot, Hibernate, Node.js, RabbitMQ, PostgreSQL, MongoDB, SQLite" />
</p>
<p>
  <b>Mobile & desktop</b><br/>
  <img src="https://skillicons.dev/icons?i=flutter,dart,kotlin,cs,dotnet" alt="Flutter, Dart, Kotlin, C#, .NET" />
</p>
<p>
  <b>Infra & tooling</b><br/>
  <img src="https://skillicons.dev/icons?i=docker,nginx,linux,githubactions,git" alt="Docker, Nginx, Linux, GitHub Actions, Git" />
  <br/>
  <img src="https://img.shields.io/badge/Proxmox_VE-E57000?style=flat-square&logo=proxmox&logoColor=white" alt="Proxmox VE" />
  <img src="https://img.shields.io/badge/Forgejo_Actions-FB923C?style=flat-square&logo=forgejo&logoColor=white" alt="Forgejo Actions" />
</p>

<details>
<summary><b>🇪🇸 Leer en español</b></summary>

<br/>

**Hola, soy Gonzalo**, desarrollador full stack en Palma de Mallorca. Construyo aplicaciones completas para web, escritorio y móvil, y también la infraestructura donde corren. Vengo de sistemas y redes, así que me gusta entender lo que pasa por debajo del framework.

**Cómo construyo:** arquitectura hexagonal (el dominio en el centro, la E/S en los bordes), Feature-Sliced Design en el frontend, SOLID aplicado de forma verificable, DRY sobre conocimiento y no sobre líneas parecidas, tests como parte de la funcionalidad, cero código muerto y decisiones documentadas en ADRs.

**Proyecto destacado:** diseñé, construí y desplegué yo solo, partiendo de cero, una plataforma de microservicios para una empresa de servicios técnicos: 5 microservicios con base de datos por servicio, IAM con JWT y RBAC, RabbitMQ con Transactional Outbox, portales PWA en React, más de 500 tests automatizados y CI/CD propio en Forgejo Actions sobre Proxmox VE.

**Proyectos:** Quotidia (planificador diario en Flutter), License Generator (licencias firmadas con RSA, .NET + Avalonia), NutriManager (gestión para nutricionistas), Kanban Board y Pokédex (React + TypeScript).

¿Hablamos? → [Portfolio](https://mi-portafolio-gonzalo.vercel.app/) · [LinkedIn](https://www.linkedin.com/in/gonzalo-martinez-garcia-353507370)

</details>

---

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/gonzapersonalsite/gonzapersonalsite/output/github-snake-dark.svg" />
  <img src="https://raw.githubusercontent.com/gonzapersonalsite/gonzapersonalsite/output/github-snake.svg" alt="Snake eating my contribution graph" />
</picture>

<sub>No contributions were harmed in the making of this snake. 🐍</sub>

</div>
