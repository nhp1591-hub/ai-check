document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const scoreButton = document.getElementById('scoreButton');
    const loading = document.getElementById('loading');
    const resultsSection = document.getElementById('resultsSection');
    const errorMessage = document.getElementById('errorMessage');
    const successMessage = document.getElementById('successMessage');

    // 파일 선택 시 버튼 활성화
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            scoreButton.disabled = false;
            scoreButton.textContent = '채점 시작';
            hideMessages();
        } else {
            scoreButton.disabled = true;
            scoreButton.textContent = '엑셀 파일을 선택하세요';
        }
    });

    // 채점 버튼 클릭
    scoreButton.addEventListener('click', function() {
        if (fileInput.files.length === 0) {
            showError('엑셀 파일을 선택해주세요.');
            return;
        }

        const file = fileInput.files[0];
        if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
            showError('엑셀 파일(.xlsx 또는 .xls)만 업로드 가능합니다.');
            return;
        }

        startScoring(file);
    });

    function startScoring(file) {
        // UI 상태 변경
        scoreButton.disabled = true;
        scoreButton.textContent = '채점 중...';
        loading.style.display = 'block';
        resultsSection.style.display = 'none';
        hideMessages();

        // 파일을 Base64로 인코딩
        const reader = new FileReader();
        reader.onload = function(e) {
            const base64Data = e.target.result.split(',')[1];
            
            // 서버로 데이터 전송
            fetch('/api/score', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_data: base64Data,
                    filename: file.name
                })
            })
            .then(response => response.json())
            .then(data => {
                loading.style.display = 'none';
                scoreButton.disabled = false;
                scoreButton.textContent = '채점 시작';

                if (data.success) {
                    displayResults(data);
                    showSuccess('채점이 완료되었습니다!');
                } else {
                    showError(data.error || '채점 중 오류가 발생했습니다.');
                }
            })
            .catch(error => {
                loading.style.display = 'none';
                scoreButton.disabled = false;
                scoreButton.textContent = '채점 시작';
                showError('서버 연결 오류가 발생했습니다. 다시 시도해주세요.');
                console.error('Error:', error);
            });
        };

        reader.readAsDataURL(file);
    }

    function displayResults(data) {
        const tableBody = document.getElementById('resultsTableBody');
        const expandedContainer = document.getElementById('expandedFeedbackContainer');
        
        // 기존 내용 완전 제거
        tableBody.innerHTML = '';
        expandedContainer.innerHTML = '';

        // 전역 변수에 결과 저장 (다운로드용)
        window.currentResults = data;

        data.results.forEach((result, index) => {
            const row = document.createElement('tr');
            row.style.margin = '0';
            row.style.padding = '0';
            
            // 피드백 텍스트 생성
            let feedbackText = '-';
            let hasFeedback = false;
            
            if (result.success && result.score.feedback) {
                feedbackText = result.score.feedback;
                hasFeedback = true;
            } else if (!result.success && result.error) {
                feedbackText = result.error;
                hasFeedback = true;
            }

            // 등급에 따른 클래스 설정
            const gradeClass = result.score.grade === 'A' ? 'grade-a' : 
                              result.score.grade === 'B' ? 'grade-b' : 'grade-c';
            
            const scoreText = result.success ? `${result.score.total_score}점` : '채점 실패';

            // 피드백 셀 HTML 생성 - index 사용
            let feedbackCellHTML = '';
            if (hasFeedback) {
                const shortText = feedbackText.length > 50 ? feedbackText.substring(0, 50) + '...' : feedbackText;
                feedbackCellHTML = `
                    <div class="feedback-preview">${shortText}</div>
                    <button class="feedback-toggle" data-index="${index}" onclick="toggleFeedback(${index})" title="피드백 보기">
                        <span class="arrow">▼</span>
                    </button>
                `;
            } else {
                feedbackCellHTML = `<div class="feedback-preview">${feedbackText}</div>`;
            }

            // 테이블 셀 생성 - 불필요한 공간 제거
            row.innerHTML = `
                <td style="margin: 0; padding: 12px 15px;">${result.index}</td>
                <td style="margin: 0; padding: 12px 15px;">${result.department}</td>
                <td style="margin: 0; padding: 12px 15px;">${result.name}</td>
                <td style="margin: 0; padding: 12px 15px; line-height: 1.3;">${result.task_name}</td>
                <td style="margin: 0; padding: 12px 15px;">
                    <span class="score-badge ${gradeClass}">
                        ${result.score.grade} (${scoreText})
                    </span>
                </td>
                <td style="margin: 0; padding: 12px 15px;">${result.success ? '성공' : '실패'}</td>
                <td style="margin: 0; padding: 12px 15px;">${feedbackCellHTML}</td>
            `;
            
            tableBody.appendChild(row);

            // 확장된 피드백 컨테이너를 해당 행 바로 다음에 생성
            if (hasFeedback) {
                const expandedFeedback = document.createElement('tr');
                expandedFeedback.className = 'expanded-feedback-row';
                expandedFeedback.id = `expanded-feedback-${index}`;
                expandedFeedback.style.display = 'none';
                expandedFeedback.innerHTML = `
                    <td colspan="7" style="padding: 0; border: none;">
                        <div class="expanded-feedback-content">
                            <div class="feedback-content-full">${feedbackText.replace(/\n/g, '<br>')}</div>
                        </div>
                    </td>
                `;
                tableBody.appendChild(expandedFeedback);
            }
        });

        // 통계 업데이트
        updateStatistics(data);
    }

    function updateStatistics(data) {
        const { statistics } = data;
        document.getElementById('totalEntries').textContent = statistics.total_entries;
        document.getElementById('successfulEntries').textContent = statistics.successful_entries;
        document.getElementById('successRate').textContent = statistics.success_rate.toFixed(1);
        document.getElementById('averageScore').textContent = statistics.average_score.toFixed(1);
        document.getElementById('maxScore').textContent = statistics.max_score;
        document.getElementById('minScore').textContent = statistics.min_score;

        // 등급 분포 표시
        const gradeDistribution = statistics.grade_distribution;
        document.getElementById('gradeACount').textContent = gradeDistribution.A || 0;
        document.getElementById('gradeBCount').textContent = gradeDistribution.B || 0;
        document.getElementById('gradeCCount').textContent = gradeDistribution.C || 0;

        // 결과 섹션 표시
        resultsSection.style.display = 'block';
    }

    function getGradeClass(grade) {
        switch(grade) {
            case 'A': return 'score-a';
            case 'B': return 'score-b';
            case 'C': return 'score-c';
            default: return 'score-c';
        }
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        successMessage.style.display = 'none';
    }

    function showSuccess(message) {
        successMessage.textContent = message;
        successMessage.style.display = 'block';
        errorMessage.style.display = 'none';
    }

    function hideMessages() {
        errorMessage.style.display = 'none';
        successMessage.style.display = 'none';
    }

    // 샘플 파일 다운로드
    window.downloadSample = function() {
        const sampleData = [
            ['부서', '성명', '사번', '과제명', '과제소개', '과제링크 제출'],
            ['디지털전략부', '홍길동', '123456', 'AI 활용 업무 개선', '일상 업무에 AI를 활용하여 효율성을 높이는 방안', 'https://chatgpt.com/share/example1'],
            ['마케팅팀', '김철수', '234567', '고객 서비스 자동화', '고객 문의에 대한 자동 응답 시스템 구축', 'https://chatgpt.com/share/example2'],
            ['개발팀', '이영희', '345678', '코드 리뷰 도구', 'AI를 활용한 코드 품질 검토 시스템', 'https://chatgpt.com/share/example3']
        ];

        // CSV 형식으로 변환
        const csvContent = sampleData.map(row => row.join(',')).join('\n');
        
        // 파일 다운로드
        const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', 'AI_리터러시_채점_샘플.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // 결과 다운로드
    window.downloadResults = function(format) {
        const results = window.currentResults;
        if (!results) {
            showError('다운로드할 결과가 없습니다.');
            return;
        }

        if (format === 'csv') {
            downloadCSV(results);
        } else if (format === 'excel') {
            downloadExcel(results);
        }
    };

    function downloadCSV(data) {
        const headers = ['번호', '부서', '성명', '과제명', '등급', '점수', '피드백', '성공여부'];
        const csvData = [headers];

        data.results.forEach(result => {
            // 피드백 텍스트 생성
            let feedbackText = '-';
            if (result.success && result.score.feedback) {
                feedbackText = result.score.feedback;
            } else if (!result.success && result.error) {
                feedbackText = result.error;
            }
            
            csvData.push([
                result.index,
                result.department,
                result.name,
                result.task_name,
                result.score.grade,
                result.success ? result.score.total_score : '채점 실패',
                feedbackText,
                result.success ? '성공' : '실패'
            ]);
        });

        const csvContent = csvData.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
        const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
        downloadBlob(blob, 'AI_리터러시_채점_결과.csv');
    }

    function downloadExcel(data) {
        // Excel 다운로드는 서버에서 처리
        const requestData = {
            results: data.results,
            format: 'excel'
        };

        fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.blob())
        .then(blob => {
            downloadBlob(blob, 'AI_리터러시_채점_결과.xlsx');
        })
        .catch(error => {
            showError('파일 다운로드 중 오류가 발생했습니다.');
            console.error('Download error:', error);
        });
    }

    function downloadBlob(blob, filename) {
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
});

// 피드백 토글 함수 (전역 함수로 설정)
function toggleFeedback(resultIndex) {
    console.log('Toggle feedback called with index:', resultIndex);
    
    const feedbackContent = document.getElementById(`expanded-feedback-${resultIndex}`);
    const toggleButton = document.querySelector(`button[data-index="${resultIndex}"]`);
    
    console.log('Found elements:', { feedbackContent, toggleButton });
    
    if (!feedbackContent || !toggleButton) {
        console.error('Feedback elements not found:', { resultIndex, feedbackContent, toggleButton });
        return;
    }
    
    const arrow = toggleButton.querySelector('.arrow');
    
    if (feedbackContent.classList.contains('show')) {
        // 접기
        console.log('Collapsing feedback');
        feedbackContent.classList.remove('show');
        feedbackContent.style.display = 'none';
        arrow.textContent = '▼';
        toggleButton.classList.remove('expanded');
    } else {
        // 펼치기
        console.log('Expanding feedback');
        feedbackContent.classList.add('show');
        feedbackContent.style.display = 'block';
        arrow.textContent = '▲';
        toggleButton.classList.add('expanded');
    }
} 