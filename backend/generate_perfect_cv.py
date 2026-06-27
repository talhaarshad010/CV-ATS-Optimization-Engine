import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf():
    pdf_path = "/Users/muhammadtalhaarshad/Downloads/cv-platform/frontend/assets/Ali_Shair_CV.pdf"
    
    # Setup document
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles to fit standard flow
    name_style = ParagraphStyle(
        'NameStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1d1d1f'),
        alignment=0, # Left aligned
        spaceAfter=4
    )
    
    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#6e6e73'),
        alignment=0,
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'H1Style',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        textColor=colors.HexColor('#1d1d1f'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#3a3a3c'),
        spaceAfter=4
    )
    
    story = []
    
    # Header Info (Name, Contact Details, Location, LinkedIn)
    story.append(Paragraph("Ali Shair", name_style))
    story.append(Paragraph("Email: alishair@example.com | Phone: +92 300 1234567 | Location: Karachi, Pakistan | LinkedIn: linkedin.com/in/alishair | GitHub: github.com/alishair", contact_style))
    
    # 1. Summary Section
    story.append(Paragraph("Professional Summary", h1_style))
    story.append(Paragraph(
        "Highly motivated and result-oriented Software Engineer with over 4 years of hands-on experience in building scalable web applications, RESTful APIs, and cross-platform mobile solutions. Proven track record of leveraging technologies like Python, FastAPI, and React to deliver high-impact products and optimize operational performance.",
        body_style
    ))
    
    # 2. Education Section
    story.append(Paragraph("Education", h1_style))
    story.append(Paragraph(
        "<b>SZABIST University</b> — Karachi, Pakistan<br/>"
        "Bachelor of Science in Computer Science (CGPA: 3.82) | 08/2020 - 06/2024<br/>"
        "Relevant Coursework: Data Structures and Algorithms, Object-Oriented Programming, Database Management Systems, Software Engineering, Operating Systems, Computer Networks.",
        body_style
    ))
    
    # 3. Work Experience Section
    story.append(Paragraph("Work Experience", h1_style))
    # Job 1
    story.append(Paragraph(
        "<b>Logic Loops Solutions</b> — Senior Software Developer (06/2024 - Present)<br/>"
        "• Led a cross-functional team to design and deploy 4 scalable web portals using Python and React.<br/>"
        "• Reduced backend response times by 30% by refactoring core FastAPI services and optimizing SQL database queries.<br/>"
        "• Mentored junior developers on software engineering best practices, code reviews, and automated CI/CD pipeline deployments.",
        body_style
    ))
    story.append(Spacer(1, 4))
    # Job 2
    story.append(Paragraph(
        "<b>Code Master Innovative</b> — Junior Developer (08/2022 - 05/2024)<br/>"
        "• Built responsive interfaces using React.js and TypeScript, increasing user retention by 15%.<br/>"
        "• Integrated secure multi-role user authentication and data serialization layers with PostgreSQL database backend.<br/>"
        "• Implemented unit testing suites covering over 85% of critical application logic routes.",
        body_style
    ))
    
    # 4. Technical Skills Section
    story.append(Paragraph("Technical Skills", h1_style))
    story.append(Paragraph(
        "<b>Languages:</b> Python, JavaScript, TypeScript, SQL, C++, Java, HTML, CSS<br/>"
        "<b>Frameworks & Libraries:</b> React, React Native, FastAPI, Node.js, Express, Django, Pandas, NumPy<br/>"
        "<b>Tools & Databases:</b> Git, GitHub, Docker, Postman, VS Code, PostgreSQL, MongoDB, SQLite, Redis",
        body_style
    ))
    
    # 5. Projects Section
    story.append(Paragraph("Projects", h1_style))
    story.append(Paragraph(
        "<b>Customer Churn Prediction System</b><br/>"
        "• Engineered a machine learning model using Python and Scikit-Learn to predict customer subscription cancellation rates.<br/>"
        "• Designed an interactive data visualization dashboard using Streamlit to present model parameters to business clients.<br/>"
        "• Cleaned, preprocessed, and encoded 10,000+ subscriber records to optimize accuracy.",
        body_style
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>Automated Web Scraping Pipeline</b><br/>"
        "• Built modular scraping bots using BeautifulSoup and Requests to collect pricing metrics across 5 e-commerce sites.<br/>"
        "• Created cron job routines to store collected unstructured data directly into structured PostgreSQL tables.",
        body_style
    ))
    
    # 6. Certifications Section
    story.append(Paragraph("Certifications", h1_style))
    story.append(Paragraph(
        "• Google Data Analytics Professional Certificate — Coursera (Issued: 2024)<br/>"
        "• Google Cybersecurity Professional Certificate — Coursera (Issued: 2023)<br/>"
        "• Advanced React Developer Accreditation — Meta Coursework (Issued: 2023)",
        body_style
    ))
    
    # 7. Languages Section
    story.append(Paragraph("Languages", h1_style))
    story.append(Paragraph(
        "• English (Professional Working Proficiency)<br/>"
        "• Urdu (Native Proficiency)<br/>"
        "• Sindhi (Professional Working Proficiency)",
        body_style
    ))
    
    # 8. Achievements Section
    story.append(Paragraph("Achievements", h1_style))
    story.append(Paragraph(
        "• Awarded Employee of the Month at Logic Loops Solutions for outstanding platform deliveries in Q3 2025.<br/>"
        "• Won 1st Prize at University Hackathon for developing a smart utility payment assistant application in a 24-hour sprint.<br/>"
        "• Graduated with honors distinction from SZABIST Computer Science Department.",
        body_style
    ))
    
    # Build PDF
    doc.build(story)
    print(f"Successfully generated PDF CV at: {pdf_path}")

if __name__ == "__main__":
    generate_pdf()
